#!/usr/bin/env python
# coding: utf-8

import math

import fte.encoder
import marionette.record_layer

MAX_CELL_LENGTH_IN_BITS = (2 ** 18) * 8


def send_async(channel, marionette_state, input_args):
    send(channel, marionette_state, input_args, blocking=False)
    return True


def recv_async(channel, marionette_state, input_args):
    recv(channel, marionette_state, input_args, blocking=False)
    return True


def send(channel, marionette_state, input_args, blocking=True):
    retval = False

    regex = input_args[0]
    msg_len = int(input_args[1])

    stream_id = marionette_state.get_global(
        "multiplexer_outgoing").has_data_for_any_stream()
    if stream_id or blocking:

        fteObj = marionette_state.get_fte_obj(regex, msg_len)

        bits_in_buffer = len(
            marionette_state.get_global("multiplexer_outgoing").peek(stream_id)) * 8
        min_cell_len_in_bytes = int(math.floor(fteObj.getCapacity() / 8.0)) \
            - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTEXT \
            - fte.encrypter.Encrypter._CTXT_EXPANSION
        min_cell_len_in_bits = min_cell_len_in_bytes * 8

        cell_headers_in_bits = marionette.record_layer.PAYLOAD_HEADER_SIZE_IN_BITS
        cell_len_in_bits = max(min_cell_len_in_bits, bits_in_buffer)
        cell_len_in_bits = min(cell_len_in_bits + cell_headers_in_bits,
                               MAX_CELL_LENGTH_IN_BITS)

        cell = marionette_state.get_global("multiplexer_outgoing").pop(
            marionette_state.get_local("model_uuid"),
            marionette_state.get_local("model_instance_id"),
            cell_len_in_bits)
        ptxt = cell.to_string()
        # Convert string to bytes using latin-1 encoding (preserves byte values 0-255)
        if isinstance(ptxt, str):
            ptxt = ptxt.encode('latin-1')

        ctxt = fteObj.encode(ptxt)
        # FTE.encode() returns bytes, ensure it stays as bytes for channel.sendall()
        if not isinstance(ctxt, bytes):
            ctxt = ctxt.encode('latin-1') if isinstance(ctxt, str) else bytes(ctxt)
        ctxt_len = len(ctxt)
        bytes_sent = channel.sendall(ctxt)
        retval = (ctxt_len == bytes_sent)

    return retval


def recv(channel, marionette_state, input_args, blocking=True):
    retval = False
    regex = input_args[0]
    msg_len = int(input_args[1])

    fteObj = marionette_state.get_fte_obj(regex, msg_len)

    try:
        ctxt = channel.recv()
        if len(ctxt) > 0:
            # Convert string to bytes using latin-1 encoding (preserves byte values 0-255)
            if isinstance(ctxt, str):
                ctxt = ctxt.encode('latin-1')
            [ptxt, remainder] = fteObj.decode(ctxt)
            # Convert bytes back to string for compatibility
            if isinstance(ptxt, bytes):
                ptxt = ptxt.decode('latin-1')
            if isinstance(remainder, bytes):
                remainder = remainder.decode('latin-1')

            cell_obj = marionette.record_layer.unserialize(ptxt)
            assert cell_obj.get_model_uuid() == marionette_state.get_local(
                "model_uuid")

            marionette_state.set_local(
                "model_instance_id", cell_obj.get_model_instance_id())

            if marionette_state.get_local("model_instance_id"):
                if cell_obj.get_stream_id() > 0:
                    marionette_state.get_global(
                        "multiplexer_incoming").push(ptxt)
                retval = True
    except fte.encrypter.RecoverableDecryptionError as e:
        retval = False
    except Exception as e:
        if len(ctxt)>0:
            channel.rollback()
        raise e

    if retval:
        if len(remainder) > 0:
            channel.rollback(len(remainder))
    else:
        if len(ctxt)>0:
            channel.rollback()

    return retval
