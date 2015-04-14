#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading

import marionette.driver
import marionette.record_layer


class MarionetteStream(object):
    def __init__(self, multiplexer_incoming, multiplexer_outgoing, stream_id):
        self.multiplexer_incoming_ = multiplexer_incoming
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.stream_id_ = stream_id
        self.buffer_ = ''

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
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                stream_id = cell_obj.get_stream_id()
                if stream_id == 0:
                    continue
                payload = cell_obj.get_payload()
                self.streams_[stream_id].buffer_ += payload

    def stop(self):
        self.running_.clear()

    def start_new_stream(self):
        stream = MarionetteStream(self.multiplexer_incoming_,
                                  self.multiplexer_outgoing_,
                                  self.stream_counter_)
        self.streams_[self.stream_counter_] = stream
        self.stream_counter_ += 1
        return stream

    def get_stream(self, stream_id):
        return self.streams_.get(stream_id)

    def get_streams(self):
        return self.streams_


class Server(threading.Thread):
    def __init__(self, format_name):
        super(Server, self).__init__()
        self.buffer_ = ""
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.format_name_ = format_name
        self.streams_ = {}
        self.running_ = threading.Event()

        self.buffer_ = ""
        self.driver_ = marionette.driver.Driver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

    def run(self):
        self.running_.set()
        while self.running_.is_set() and True:
            self.driver_.execute()
            time.sleep(0)
            self.process_multiplexer_incoming()
            time.sleep(0)

        self.driver_.stop()

    def process_multiplexer_incoming(self):
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                stream_id = cell_obj.get_stream_id()
                payload = cell_obj.get_payload()
                if not self.streams_.get(stream_id):
                    self.streams_[stream_id] = MarionetteStream(
                        self.multiplexer_incoming_, self.multiplexer_outgoing_,
                        stream_id)
                self.streams_[stream_id].buffer_ += payload

    def stop(self):
        self.running_.clear()

    def get_stream(self, stream_id):
        if not self.streams_.get(stream_id):
            self.streams_[stream_id] = MarionetteStream(
                self.multiplexer_incoming_, self.multiplexer_outgoing_,
                stream_id)
        return self.streams_.get(stream_id)

    def get_streams(self):
        return self.streams_
