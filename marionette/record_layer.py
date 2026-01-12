#!/usr/bin/env python
# -*- coding: utf-8 -*-

import binascii
from functools import total_ordering

PAYLOAD_HEADER_SIZE_IN_BITS = 200
PAYLOAD_HEADER_SIZE_IN_BYTES = PAYLOAD_HEADER_SIZE_IN_BITS // 8

NORMAL = 0x1
END_OF_STREAM = 0x2
NEGOTIATE = 0x3


@total_ordering
class Cell(object):

    def __init__(self, model_uuid, model_instance_id, stream_id, seq_id,
                 length=0, cell_type=NORMAL):
        assert stream_id is not None

        self.cell_type_ = cell_type
        self.payload_ = ''
        self.payload_length_ = 0
        self.sequence_id_ = seq_id
        self.cell_length_ = length
        self.stream_id_ = stream_id
        self.model_uuid_ = model_uuid
        self.model_instance_id_ = model_instance_id

    def __lt__(self, other):
        return self.get_seq_id() < other.get_seq_id()

    def __eq__(self, other):
        retval = (
            self.get_payload() == other.get_payload()) and (
            self.get_stream_id() == other.get_stream_id()) and (
            self.get_model_uuid() == other.get_model_uuid()) and (
                self.get_model_instance_id() == other.get_model_instance_id()) and (
                    self.get_seq_id() == other.get_seq_id())
        return retval

    def get_cell_type(self):
        return self.cell_type_

    def get_payload(self):
        return str(self.payload_)

    def set_payload(self, payload):
        self.payload_ = payload

    def get_stream_id(self):
        return int(self.stream_id_)

    def get_model_uuid(self):
        return self.model_uuid_

    def get_model_instance_id(self):
        return self.model_instance_id_

    def get_seq_id(self):
        return int(self.sequence_id_)

    def is_valid(self):
        retval = True
        return retval

    def to_string(self):
        return serialize(self, self.cell_length_)


class EndOfStreamException(Exception):

    def set_stream_id(self, stream_id):
        self.stream_id_ = stream_id

    def get_stream_id(self):
        return self.stream_id_


def pad_to_bytes(n, val):
    val = str(val)
    while len(val) < n:
        val = '\x00' + val
    return val


def long_to_bytes(N, blocksize=1):
    """Given an input integer ``N``, ``long_to_bytes`` returns the representation of ``N`` in bytes.
    If ``blocksize`` is greater than ``1`` then the output string will be right justified and then padded with zero-bytes,
    such that the return values length is a multiple of ``blocksize``.
    """

    bytestring = hex(N)
    bytestring = bytestring[2:] if bytestring.startswith('0x') else bytestring
    bytestring = bytestring[:-1] if bytestring.endswith('L') else bytestring
    bytestring = '0' + bytestring if (len(bytestring) % 2) != 0 else bytestring
    bytestring = binascii.unhexlify(bytestring).decode('latin-1')

    if blocksize > 0 and len(bytestring) % blocksize != 0:
        bytestring = '\x00' * \
            (blocksize - (len(bytestring) % blocksize)) + bytestring

    return bytestring


def bytes_to_long(bytestring):
    """Given a ``bytestring`` returns its integer representation ``N``.
    """
    bytestring = '\x00' + bytestring
    N = int(binascii.hexlify(bytestring.encode('latin-1')), 16)
    return N


# cell format
#   total cell length - 4 bytes
#   payload length - 4 bytes
#   model uuid - 4 bytes
#   model instance id - 4 bytes
#   stream ID - 4 bytes
#   sequence ID - 4 bytes
#   cell type - 1 byte
#   payload (variable)
#   padding (variable)


def serialize(cell_obj, pad_to=0):
    retval = ''

    stream_id = cell_obj.get_stream_id()
    model_uuid = cell_obj.get_model_uuid()
    model_instance_id = cell_obj.get_model_instance_id()
    seq_id = cell_obj.get_seq_id()
    payload = cell_obj.get_payload()
    padding = '\x00' * (
        (pad_to // 8) - len(payload) - PAYLOAD_HEADER_SIZE_IN_BYTES)
    cell_type = cell_obj.get_cell_type()

    bytes_cell_len = pad_to_bytes(4, long_to_bytes(
        PAYLOAD_HEADER_SIZE_IN_BYTES + len(payload) + len(padding)))
    bytes_payload_len = pad_to_bytes(4, long_to_bytes(len(payload)))
    bytes_model_uuid = pad_to_bytes(4, long_to_bytes(model_uuid))
    bytes_model_instance_id = pad_to_bytes(4, long_to_bytes(model_instance_id))
    bytes_stream_id = pad_to_bytes(4, long_to_bytes(stream_id))
    bytes_seq_id = pad_to_bytes(4, long_to_bytes(seq_id))
    bytes_cell_type = pad_to_bytes(1, long_to_bytes(cell_type))

    retval += bytes_cell_len
    retval += bytes_payload_len
    retval += bytes_model_uuid
    retval += bytes_model_instance_id
    retval += bytes_stream_id
    retval += bytes_seq_id
    retval += bytes_cell_type
    retval += payload
    retval += padding

    assert (PAYLOAD_HEADER_SIZE_IN_BYTES + len(payload) + len(padding)
            ) == len(retval)

    return retval


def unserialize(cell_str):

    cell_len = bytes_to_long(cell_str[:4])
    payload_len = bytes_to_long(cell_str[4:8])
    model_uuid = bytes_to_long(cell_str[8:12])
    model_instance_id = bytes_to_long(cell_str[12:16])
    stream_id = bytes_to_long(cell_str[16:20])
    seq_id = bytes_to_long(cell_str[20:24])
    cell_type = bytes_to_long(cell_str[24:25])

    if cell_len != len(cell_str):
        raise UnserializeException()

    payload = cell_str[PAYLOAD_HEADER_SIZE_IN_BYTES:
                       PAYLOAD_HEADER_SIZE_IN_BYTES + payload_len]

    retval = Cell(
        model_uuid,
        model_instance_id,
        stream_id,
        seq_id,
        payload_len,
        cell_type)
    retval.set_payload(payload)

    return retval


class UnserializeException(Exception):
    pass
