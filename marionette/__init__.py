#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import threading

import marionette.driver
import marionette.multiplexer
import marionette.record_layer


class Client(object):
    def __init__(self, format_name):
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.format_name_ = format_name
        self.streams_ = {}
        self.stream_counter_ = 1

        self.driver = marionette.driver.Driver("client")
        self.driver.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver.setFormat(self.format_name_)

    def do_one_run(self, reactor=None):
        if not self.driver.isRunning():
            self.driver.reset()

        if self.driver.isRunning():
            self.driver.execute()
            self.process_multiplexer_incoming()

        if reactor:
            reactor.callFromThread(self.do_one_run, reactor)

    # change to async call
    def process_multiplexer_incoming(self):
        if self.multiplexer_incoming_.has_data():
            cell_obj = self.multiplexer_incoming_.pop()
            if cell_obj:
                stream_id = cell_obj.get_stream_id()
                if stream_id == 0:
                    return
                payload = cell_obj.get_payload()
                if payload:
                    if self.streams_[stream_id].srv_queue:
                        self.streams_[stream_id].srv_queue.put(payload)
                    else:
                        self.streams_[stream_id].buffer_ += payload

    def start_new_stream(self, srv_queue=None):
        stream = marionette.multiplexer.MarionetteStream(self.multiplexer_incoming_,
                                  self.multiplexer_outgoing_,
                                  self.stream_counter_,
                                  srv_queue)
        self.streams_[self.stream_counter_] = stream
        self.stream_counter_ += 1
        return stream


class Server(object):
    factory = None

    def __init__(self, format_name):
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.format_name_ = format_name
        self.streams_ = {}
        self.streams_lock_ = threading.RLock()
        self.running_ = threading.Event()

        self.driver_ = marionette.driver.Driver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

        self.factory_instances = {}

    def do_one_run(self, reactor=None):
        self.driver_.execute()
        self.process_multiplexer_incoming()
        if reactor:
            reactor.callFromThread(self.do_one_run, reactor)

    # change to async call
    def process_multiplexer_incoming(self):
        if self.multiplexer_incoming_.has_data():
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
                            self.streams_[stream_id] = marionette.multiplexer.MarionetteStream(
                                self.multiplexer_incoming_, self.multiplexer_outgoing_,
                                stream_id)

                            if self.factory:
                                self.factory_instances[stream_id] = self.factory()
                                self.factory_instances[stream_id].connectionMade(self.streams_[stream_id])
                        if payload:
                            self.streams_[stream_id].buffer_ += payload
                            if self.factory:
                                self.factory_instances[stream_id].dataReceived(payload)
