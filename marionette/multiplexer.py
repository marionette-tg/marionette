#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import threading
import heapq
import time

from twisted.internet import reactor
from twisted.python import log

import marionette.record_layer


class MarionetteStream(object):

    def __init__(
            self,
            multiplexer_incoming,
            multiplexer_outgoing,
            stream_id,
            srv_queue=None):
        self.multiplexer_incoming_ = multiplexer_incoming
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.stream_id_ = stream_id
        self.srv_queue = srv_queue
        self.buffer_ = ''
        self.host = None

    def terminate(self):
        self.multiplexer_outgoing_.terminate(self.stream_id_)
        if self.host:
            self.host.terminate(self.stream_id_)

    def get_stream_id(self):
        return self.stream_id_

    def push(self, data):
        self.multiplexer_outgoing_.push(self.stream_id_, data)

    def pop(self):
        retval = self.buffer_
        self.buffer_ = ''
        return retval

    def peek(self):
        return self.buffer_


class BufferOutgoing(object):

    def __init__(self):
        self.fifo_ = {}
        self.terminate_ = set()
        self.streams_with_data_ = set()
        self.sequence_nums = {}
        self.lock_ = threading.RLock()

    def push(self, stream_id, s):
        with self.lock_:
            if not self.fifo_.get(stream_id):
                self.fifo_[stream_id] = ''
            # Convert bytes to string using latin-1 encoding (preserves byte values 0-255)
            if isinstance(s, bytes):
                s = s.decode('latin-1')
            self.fifo_[stream_id] += s

            if s:
                self.streams_with_data_.add(stream_id)

            return True

    def pop(self, model_uuid, model_instance_id, n=0):
        with self.lock_:
            assert model_uuid is not None
            assert model_instance_id is not None

            cell_obj = None

            stream_id = 0
            interesting = self.streams_with_data_.union(self.terminate_)
            if len(list(interesting)) > 0:
                stream_id = random.choice(list(interesting))

            if not self.sequence_nums.get(stream_id):
                self.sequence_nums[stream_id] = 1
            if stream_id == 0:
                sequence_id = 1
            else:
                sequence_id = self.sequence_nums[stream_id]
                self.sequence_nums[stream_id] += 1

            # determine if we should terminate the stream
            if self.fifo_.get(
                    stream_id) == '' and stream_id in self.terminate_:
                cell_obj = marionette.record_layer.Cell(
                    model_uuid,
                    model_instance_id,
                    stream_id,
                    sequence_id,
                    n,
                    marionette.record_layer.END_OF_STREAM)

                self.terminate_.remove(stream_id)
                del self.fifo_[stream_id]
                del self.sequence_nums[stream_id]
                return cell_obj

            if n > 0:
                if self.has_data(stream_id):
                    cell_obj = marionette.record_layer.Cell(
                        model_uuid,
                        model_instance_id,
                        stream_id,
                        sequence_id,
                        n)
                    payload_length = (
                        n - marionette.record_layer.PAYLOAD_HEADER_SIZE_IN_BITS) // 8
                    payload = self.fifo_[stream_id][:payload_length]
                    self.fifo_[stream_id] = self.fifo_[
                        stream_id][payload_length:]
                    cell_obj.set_payload(payload)
                else:
                    cell_obj = marionette.record_layer.Cell(
                        model_uuid,
                        model_instance_id,
                        0,
                        sequence_id,
                        n)
            else:
                if self.has_data(stream_id):
                    cell_obj = marionette.record_layer.Cell(
                        model_uuid,
                        model_instance_id,
                        stream_id,
                        sequence_id)
                    payload_length = len(self.fifo_[stream_id])
                    payload = self.fifo_[stream_id][:payload_length]
                    self.fifo_[stream_id] = self.fifo_[
                        stream_id][payload_length:]
                    cell_obj.set_payload(payload)

            if self.fifo_.get(stream_id) == '':
                self.streams_with_data_.remove(stream_id)

            return cell_obj

    def peek(self, stream_id):
        retval = ''
        with self.lock_:
            if self.fifo_.get(stream_id):
                retval = self.fifo_.get(stream_id)
        return retval

    def has_data(self, stream_id):
        retval = False
        with self.lock_:
            if self.fifo_.get(stream_id):
                retval = len(self.fifo_[stream_id]) > 0
        return retval

    def has_data_for_any_stream(self):
        retval = None
        with self.lock_:
            if len(self.streams_with_data_) > 0:
                retval = random.choice(list(self.streams_with_data_))
        return retval

    def terminate(self, stream_id):
        with self.lock_:
            self.terminate_.add(stream_id)


class BufferIncoming(object):

    # Default timeout for orphaned streams (seconds)
    DEFAULT_STREAM_TIMEOUT = 300  # 5 minutes

    def __init__(self, stream_timeout=None):
        self.fifo_ = ''
        self.fifo_len_ = 0
        self.output_q = {}
        self.curr_seq_id = {}
        self.stream_last_activity = {}  # Track last activity time for each stream
        self.stream_timeout = stream_timeout or self.DEFAULT_STREAM_TIMEOUT
        self.has_data_ = False
        self.callback_ = None
        self.lock_ = threading.RLock()

    def addCallback(self, callback):
        with self.lock_:
            self.callback_ = callback

    def dequeue(self, cell_stream_id):
        with self.lock_:
            # Update last activity time
            self.stream_last_activity[cell_stream_id] = time.time()
            
            remove_keys = set()
            while (len(self.output_q[cell_stream_id]) > 0 and
                self.output_q[cell_stream_id][0].get_seq_id() == self.curr_seq_id[cell_stream_id]):
                
                cell_obj = heapq.heappop(self.output_q[cell_stream_id])
                self.curr_seq_id[cell_stream_id] += 1

                log.msg("Stream %d Dequeue ID %d" % 
                    (cell_stream_id,cell_obj.get_seq_id()))

                if cell_obj.get_cell_type() == marionette.record_layer.END_OF_STREAM:
                    log.msg("Removing Stream %d" % (cell_stream_id))
                    remove_keys.add(cell_stream_id)

                reactor.callFromThread(self.callback_, cell_obj)

            for key in remove_keys:
                self._cleanup_stream(key)

    def enqueue(self, cell_obj, cell_stream_id):
        with self.lock_:
            # Update last activity time
            self.stream_last_activity[cell_stream_id] = time.time()
            
            if cell_stream_id not in self.output_q:
                self.output_q[cell_stream_id] = []
                self.curr_seq_id[cell_stream_id] = 1
            heapq.heappush(self.output_q[cell_stream_id],cell_obj)
            log.msg("Stream %d Enqueue ID %d" % (cell_stream_id,cell_obj.get_seq_id()))

    def push(self, s):
        with self.lock_:
            # Convert bytes to string using latin-1 encoding (preserves byte values 0-255)
            if isinstance(s, bytes):
                s = s.decode('latin-1')
            self.fifo_ += s
            self.fifo_len_ += len(s)

        if self.callback_:
            while True:
                cell_obj = self.pop()
                if cell_obj:
                    cell_stream_id = cell_obj.get_stream_id()
                    if cell_stream_id > 0:
                        self.enqueue(cell_obj, cell_stream_id)
                        self.dequeue(cell_stream_id)
                    else:
                        reactor.callFromThread(self.callback_, cell_obj)
                    continue
                else:
                    break

        return True

    def pop(self):
        with self.lock_:
            cell_obj = None

            if len(self.fifo_) >= 8:
                cell_len = marionette.record_layer.bytes_to_long(
                    str(self.fifo_[:4]))
                cell_obj = marionette.record_layer.unserialize(
                    self.fifo_[:cell_len])
                self.fifo_ = self.fifo_[cell_len:]
                self.fifo_len_ -= cell_len
                self.fifo_len_ = max(self.fifo_len_, 0)

        return cell_obj

    def _cleanup_stream(self, stream_id):
        """Clean up resources for a stream."""
        with self.lock_:
            if stream_id in self.output_q:
                del self.output_q[stream_id]
            if stream_id in self.curr_seq_id:
                del self.curr_seq_id[stream_id]
            if stream_id in self.stream_last_activity:
                del self.stream_last_activity[stream_id]

    def cleanup_orphaned_streams(self):
        """
        Clean up streams that haven't been active for longer than the timeout.
        Returns the number of streams cleaned up.
        """
        with self.lock_:
            current_time = time.time()
            orphaned_streams = []
            
            for stream_id, last_activity in list(self.stream_last_activity.items()):
                if current_time - last_activity > self.stream_timeout:
                    orphaned_streams.append(stream_id)
            
            for stream_id in orphaned_streams:
                log.msg("Cleaning up orphaned stream %d (inactive for %.1f seconds)" %
                       (stream_id, current_time - self.stream_last_activity.get(stream_id, 0)))
                self._cleanup_stream(stream_id)
            
            return len(orphaned_streams)
