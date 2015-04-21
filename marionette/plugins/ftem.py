import socket
import math

import fte.encoder
import marionette.record_layer
import time

MAX_CELL_LENGTH_IN_BITS = (2 ** 16) * 8


def send_async(channel, global_args, local_args, input_args):
    send(channel, global_args, local_args, input_args, blocking=False)
    return True


def recv_async(channel, global_args, local_args, input_args):
    recv(channel, global_args, local_args, input_args, blocking=False)
    return True


def send(channel, global_args, local_args, input_args, blocking=True):
    retval = False

    regex = input_args[0]
    msg_len = int(input_args[1])

    stream_id = global_args["multiplexer_outgoing"].has_data_for_any_stream()
    if stream_id or blocking:
        fte_key = 'fte_key-' + regex + str(msg_len)
        fteObj = global_args[fte_key]

        bits_in_buffer = len(
            global_args["multiplexer_outgoing"].peek(stream_id)) * 8
        min_cell_len_in_bytes = int(math.floor(fteObj.getCapacity() / 8.0)) \
                               - fte.encoder.DfaEncoderObject._COVERTEXT_HEADER_LEN_CIPHERTTEXT \
                               - fte.encrypter.Encrypter._CTXT_EXPANSION
        min_cell_len_in_bits = min_cell_len_in_bytes * 8

        cell_headers_in_bits = marionette.record_layer.PAYLOAD_HEADER_SIZE_IN_BITS
        cell_len_in_bits = max(min_cell_len_in_bits, bits_in_buffer)
        cell_len_in_bits = min(cell_len_in_bits+cell_headers_in_bits,
                               MAX_CELL_LENGTH_IN_BITS)

        cell = global_args["multiplexer_outgoing"].pop(
            local_args["model_uuid"], local_args["model_instance_id"], cell_len_in_bits)
        ptxt = cell.to_string()

        ctxt = fteObj.encode(ptxt)
        ctxt_len = len(ctxt)
        while len(ctxt) > 0:
            try:
                bytes_sent = channel.send(ctxt)
                ctxt = ctxt[bytes_sent:]
            except socket.timeout:
                continue
            except socket.error:
                continue
        retval = (ctxt_len == bytes_sent)

    return retval


def recv(channel, global_args, local_args, input_args, blocking=True):
    retval = False
    regex = input_args[0]
    msg_len = int(input_args[1])

    fte_key = 'fte_key-' + regex + str(msg_len)
    fteObj = global_args[fte_key]

    try:
        ctxt = channel.recv()
        if len(ctxt) >= msg_len:
            [ptxt, remainder] = fteObj.decode(ctxt)

            cell_obj = marionette.record_layer.unserialize(ptxt)
            assert cell_obj.get_model_uuid() == local_args["model_uuid"]

            local_args["model_instance_id"] = cell_obj.get_model_instance_id()
            if local_args.get("model_instance_id"):
                if cell_obj.get_stream_id()>0:
                    global_args["multiplexer_incoming"].push(ptxt)
                retval = True
    except fte.encrypter.RecoverableDecryptionError as e:
        retval = False
    except Exception as e:
        retval = False

    if not retval:
        channel.rollback()
    else:
        if len(remainder) > 0:
            channel.rollback(len(remainder))

    return retval
