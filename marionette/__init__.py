#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading

import marionette.driver
import marionette.multiplexer
import marionette.record_layer


class MarionetteStream(object):
    def __init__(self, multiplexer_incoming, multiplexer_outgoing, stream_id, srv_queue=None):
        self.multiplexer_incoming_ = multiplexer_incoming
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.stream_id_ = stream_id
        self.srv_queue = srv_queue
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
        self.running_.set()
        while self.running_.is_set():
            while self.running_.is_set() and self.driver.isRunning():
                self.do_one_run()
            self.driver.stop()
            self.driver.reset()

    def do_one_run(self):
        if self.driver.isRunning():
            self.driver.execute()
            self.process_multiplexer_incoming()

    def process_multiplexer_incoming(self):
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                stream_id = cell_obj.get_stream_id()
                if stream_id == 0:
                    continue
                payload = cell_obj.get_payload()
                if payload:
                    if self.streams_[stream_id].srv_queue:
                        self.streams_[stream_id].srv_queue.put(payload)
                    else:
                        self.streams_[stream_id].buffer_ += payload

    def stop(self):
        self.running_.clear()

    def start_new_stream(self, srv_queue=None):
        stream = MarionetteStream(self.multiplexer_incoming_,
                                  self.multiplexer_outgoing_,
                                  self.stream_counter_,
                                  srv_queue)
        self.streams_[self.stream_counter_] = stream
        self.stream_counter_ += 1
        return stream

    def get_stream(self, stream_id):
        return self.streams_.get(stream_id)

    def get_streams(self):
        return self.streams_

    def terminate_stream(self, stream_id):
        self.multiplexer_outgoing_.terminate(stream_id)
        if self.streams_.get(stream_id):
            self.streams_[stream_id].terminate()
            del self.streams_[stream_id]


class Server(threading.Thread):
    factory = None

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

        self.factory_instances = {}

    def run(self):
        self.running_.set()
        while self.running_.is_set():
            self.do_one_run()
        self.driver_.stop()

    def do_one_run(self):
        self.driver_.execute()
        self.process_multiplexer_incoming()

    def process_multiplexer_incoming(self):
        while self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                cell_type = cell_obj.get_cell_type()
                stream_id = cell_obj.get_stream_id()
                if cell_type == marionette.record_layer.END_OF_STREAM:
                    if self.factory:
                        self.factory_instances[stream_id].connectionLost()
                        del self.factory_instances[stream_id]
                elif cell_type == marionette.record_layer.NORMAL:
                    payload = cell_obj.get_payload()
                    with self.streams_lock_:
                        if stream_id>0 and not self.streams_.get(stream_id):
                            self.streams_[stream_id] = MarionetteStream(
                                self.multiplexer_incoming_, self.multiplexer_outgoing_,
                                stream_id)

                            if self.factory:
                                self.factory_instances[stream_id] = self.factory()
                                self.factory_instances[stream_id].connectionMade(self.streams_[stream_id])
                        if payload:
                            self.streams_[stream_id].buffer_ += payload
                            if self.factory:
                                self.factory_instances[stream_id].dataReceived(payload)

    def stop(self):
        self.running_.clear()

    def get_stream(self, stream_id):
        with self.streams_lock_:
            return self.streams_.get(stream_id)

    def get_streams(self):
        with self.streams_lock_:
            return self.streams_

    def terminate_stream(self, stream_id):
        with self.streams_lock_:
            if self.streams_.get(stream_id):
                self.streams_[stream_id].terminate()
                del self.streams_[stream_id]
