#!/usr/bin/env python
# -*- coding: utf-8 -*-

import marionette.driver
import marionette.multiplexer
import marionette.record_layer


class MarionetteException(Exception):
    pass


class Client(object):
    def __init__(self, format_name):
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_multiplexer_incoming)
        self.format_name_ = format_name
        self.streams_ = {}
        self.stream_counter_ = 1

        self.driver = marionette.driver.ClientDriver("client")
        self.driver.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver.setFormat(self.format_name_)

    def execute(self, reactor=None):
        if not self.driver.isRunning():
            self.driver.reset()

        if self.driver.isRunning():
            self.driver.execute()

        if reactor:
            reactor.callInThread(self.execute, reactor)

    def process_multiplexer_incoming(self):
        cell_obj = self.multiplexer_incoming_.pop()
        if cell_obj:
            stream_id = cell_obj.get_stream_id()
            payload = cell_obj.get_payload()
            if payload:
                self.streams_[stream_id].srv_queue.put(payload)

    def start_new_stream(self, srv_queue=None):
        stream = marionette.multiplexer.MarionetteStream(self.multiplexer_incoming_,
                                  self.multiplexer_outgoing_,
                                  self.stream_counter_,
                                  srv_queue)
        stream.host = self
        self.streams_[self.stream_counter_] = stream
        self.stream_counter_ += 1
        return stream

    def terminate(self, stream_id):
        del self.streams_[stream_id]


class Server(object):
    factory = None

    def __init__(self, format_name):
        self.multiplexer_outgoing_ = marionette.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette.multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_multiplexer_incoming)
        self.format_name_ = format_name

        self.driver_ = marionette.driver.ServerDriver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

        self.factory_instances = {}

    def execute(self, reactor=None):
        self.driver_.execute()

        if reactor:
            reactor.callInThread(self.execute, reactor)

    def process_multiplexer_incoming(self):
        cell_obj = self.multiplexer_incoming_.pop()
        if cell_obj:
            cell_type = cell_obj.get_cell_type()
            stream_id = cell_obj.get_stream_id()

            if cell_type == marionette.record_layer.END_OF_STREAM:
                self.factory_instances[stream_id].connectionLost()
                del self.factory_instances[stream_id]
            elif cell_type == marionette.record_layer.NORMAL:
                if not self.factory_instances.get(stream_id):
                    stream = marionette.multiplexer.MarionetteStream(
                        self.multiplexer_incoming_, self.multiplexer_outgoing_,
                        stream_id)
                    self.factory_instances[stream_id] = self.factory()
                    self.factory_instances[stream_id].connectionMade(stream)

                payload = cell_obj.get_payload()
                if payload:
                    self.factory_instances[stream_id].dataReceived(payload)