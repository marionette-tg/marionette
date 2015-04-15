#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

import marionette.record_layer

class BufferOutgoing(object):
    def __init__(self):
        self.fifo_ = {}
        self.terminate_ = []

    def push(self, stream_id, s):
        if not self.fifo_.get(stream_id):
            self.fifo_[stream_id] = ''
        self.fifo_[stream_id] += s
        return True

    def pop(self, model_uuid, model_instance_id, sequence_id, n=0):
        assert model_uuid is not None
        assert model_instance_id is not None

        cell_obj = None

        stream_id = 0
        if len(list(self.fifo_.keys())) > 0:
            stream_id = random.choice(list(self.fifo_.keys()))

        # determine if we should terminate the stream
        if not self.fifo_.get(stream_id) and stream_id in self.terminate_:
            cell_obj = marionette.record_layer.Cell(model_uuid, model_instance_id, stream_id,
                                sequence_id, 0, marionette.record_layer.END_OF_STREAM)
            self.terminate_.remove(stream_id)
            del self.fifo_[stream_id]
            return cell_obj

        # determine if we should proceed normally
        if n > 0:
            if self.has_data(stream_id):
                cell_obj = marionette.record_layer.Cell(model_uuid, model_instance_id, stream_id,
                                sequence_id, n)
                payload_length = (n - marionette.record_layer.PAYLOAD_HEADER_SIZE_IN_BITS) / 8
                payload = self.fifo_[stream_id][:payload_length]
                self.fifo_[stream_id] = self.fifo_[stream_id][payload_length:]
                cell_obj.set_payload(payload)
            else:
                cell_obj = marionette.record_layer.Cell(model_uuid, model_instance_id, stream_id,
                                sequence_id, n)
        else:
            if self.has_data(stream_id):
                cell_obj = marionette.record_layer.Cell(model_uuid, model_instance_id, stream_id,
                                sequence_id)
                payload_length = len(self.fifo_[stream_id])
                payload = self.fifo_[stream_id][:payload_length]
                self.fifo_[stream_id] = self.fifo_[stream_id][payload_length:]
                cell_obj.set_payload(payload)

        return cell_obj

    def peek(self, stream_id):
        retval = ''
        if self.fifo_.get(stream_id):
            retval = self.fifo_.get(stream_id)
        return retval

    def has_data(self, stream_id):
        retval = False
        if self.fifo_.get(stream_id):
            retval = len(self.fifo_[stream_id]) > 0
        return retval

    def has_data_for_any_stream(self):
        retval = None
        for stream_id in list(self.fifo_.keys()):
            if len(self.fifo_[stream_id]) > 0:
                retval = stream_id
                break
        return retval

    def terminate(self, stream_id):
        self.terminate_.append(stream_id)


class BufferIncoming(object):
    def __init__(self):
        self.fifo_ = ''
        self.fifo_len_ = 0
        self.has_data_ = False

    def push(self, s):
        self.fifo_ += s
        self.fifo_len_ += len(s)
        return True

    def pop(self):
        cell_obj = None

        if len(self.fifo_) >= 8:
            cell_len = marionette.record_layer.bytes_to_long(str(self.fifo_[:4]))
            cell_obj = marionette.record_layer.unserialize(self.fifo_[:cell_len])
            self.fifo_ = self.fifo_[cell_len:]
            self.fifo_len_ -= cell_len
            self.fifo_len_ = max(self.fifo_len_, 0)

        return cell_obj

    def peek(self):
        return self.fifo_

    def has_data(self):
        return (self.fifo_len_ > 0)