#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading

import marionette.driver
import marionette.multiplexer
import marionette.record_layer


class MarionetteStream(object):
    def __init__(self, multiplexer_incoming, multiplexer_outgoing, stream_id):
        self.multiplexer_incoming_ = multiplexer_incoming
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.stream_id_ = stream_id
        self.buffer_ = ''
        self.active_ = True

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

    def terminate(self):
        self.multiplexer_outgoing_.terminate(self.stream_id_)
        self.active_ = False

    def is_active(self):
        return self.active_


class Client(threading.Thread):
    def __init__(self, format_name):
        super(Client, self).__init__()
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.format_name_ = format_name
        self.streams_ = {}
        self.stream_counter_ = 1
        self.running_ = threading.Event()

        self.driver = marionette.driver.Driver("client")
        self.driver.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver.setFormat(self.format_name_)

    def run(self):
        # TODO: make this threadsafe
        self.running_.set()
        while self.running_.is_set():
            while self.running_.is_set() and self.driver.isRunning():
                self.driver.execute()
                time.sleep(0)
                self.process_multiplexer_incoming()
                time.sleep(0)
            self.driver.stop()
            self.driver.reset()

    def process_multiplexer_incoming(self):
        # TODO: make this threadsafe
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                stream_id = cell_obj.get_stream_id()
                if stream_id == 0:
                    continue
                payload = cell_obj.get_payload()
                if payload:
                    self.streams_[stream_id].buffer_ += payload

    def stop(self):
        # TODO: make this threadsafe
        self.running_.clear()

    def start_new_stream(self):
        # TODO: make this threadsafe
        stream = MarionetteStream(self.multiplexer_incoming_,
                                  self.multiplexer_outgoing_,
                                  self.stream_counter_)
        self.streams_[self.stream_counter_] = stream
        self.stream_counter_ += 1
        return stream

    def get_stream(self, stream_id):
        # TODO: make this threadsafe
        return self.streams_.get(stream_id)

    def get_streams(self):
        # TODO: make this threadsafe
        return self.streams_

    def terminate_stream(self, stream_id):
        # TODO: make this threadsafe
        self.multiplexer_outgoing_.terminate(stream_id)
        if self.streams_.get(stream_id):
            self.streams_[stream_id].terminate()
            del self.streams_[stream_id]


class Server(threading.Thread):
    def __init__(self, format_name):
        super(Server, self).__init__()
        self.buffer_ = ""
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.format_name_ = format_name
        self.streams_ = {}
        self.streams_lock_ = threading.RLock()
        self.running_ = threading.Event()

        self.buffer_ = ""
        self.driver_ = marionette.driver.Driver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

    def run(self):
        # TODO: make this threadsafe
        self.running_.set()
        while self.running_.is_set() and True:
            self.driver_.execute()
            time.sleep(0)
            self.process_multiplexer_incoming()
            time.sleep(0)

        self.driver_.stop()

    def process_multiplexer_incoming(self):
        # TODO: make this threadsafe
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                cell_type = cell_obj.get_cell_type()
                stream_id = cell_obj.get_stream_id()
                if cell_type == marionette.record_layer.END_OF_STREAM:
                    self.terminate_stream(stream_id)
                elif cell_type == marionette.record_layer.NORMAL:
                    payload = cell_obj.get_payload()
                    with self.streams_lock_:
                        if stream_id>0 and not self.streams_.get(stream_id):
                            self.streams_[stream_id] = MarionetteStream(
                                self.multiplexer_incoming_, self.multiplexer_outgoing_,
                                stream_id)
                        if payload:
                            self.streams_[stream_id].buffer_ += payload

    def stop(self):
        self.running_.clear()

    def get_stream(self, stream_id):
        # TODO: make this threadsafe
        # if not self.streams_.get(stream_id):
        #     self.streams_[stream_id] = MarionetteStream(
        #         self.multiplexer_incoming_, self.multiplexer_outgoing_,
        #         stream_id)
        with self.streams_lock_:
            return self.streams_.get(stream_id)

    def get_streams(self):
        # TODO: make this threadsafe (i.e., protect self.streams_)
        with self.streams_lock_:
            return self.streams_

    def terminate_stream(self, stream_id):
        # TODO: figure out how to call this server side, special cell + exception?
        #self.multiplexer_outgoing_.terminate(stream_id)
        with self.streams_lock_:
            if self.streams_.get(stream_id):
                self.streams_[stream_id].terminate()
                del self.streams_[stream_id]
