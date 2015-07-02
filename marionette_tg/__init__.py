#!/usr/bin/env python
# -*- coding: utf-8 -*-

import marionette_tg.driver
import marionette_tg.multiplexer
import marionette_tg.record_layer

EVENT_LOOP_FREQUENCY_S = 0.01


class MarionetteException(Exception):
    pass


class Client(object):

    def __init__(self, format_name, format_version):
        self.multiplexer_outgoing_ = marionette_tg.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette_tg.multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_cell)
        self.format_name_ = format_name
        self.format_version_ = format_version
        self.streams_ = {}
        self.stream_counter_ = 1

        self.driver_ = marionette_tg.driver.ClientDriver("client")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_, self.format_version_)

    def execute(self, reactor):
        if self.driver_.isRunning():
            self.driver_.execute(reactor)
        else:
            self.driver_.reset()

        reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def process_cell(self, cell_obj):
        payload = cell_obj.get_payload()
        if payload:
            stream_id = cell_obj.get_stream_id()
            self.streams_[stream_id].srv_queue.put(payload)

    def start_new_stream(self, srv_queue=None):
        stream = marionette_tg.multiplexer.MarionetteStream(
            self.multiplexer_incoming_,
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
        self.multiplexer_outgoing_ = marionette_tg.multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = marionette_tg.multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_cell)
        self.format_name_ = format_name

        self.driver_ = marionette_tg.driver.ServerDriver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

        self.factory_instances = {}

    def execute(self, reactor):
        self.driver_.execute(reactor)

        reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def process_cell(self, cell_obj):
        cell_type = cell_obj.get_cell_type()
        stream_id = cell_obj.get_stream_id()

        if cell_type == marionette_tg.record_layer.END_OF_STREAM:
            self.factory_instances[stream_id].connectionLost()
            del self.factory_instances[stream_id]
        elif cell_type == marionette_tg.record_layer.NORMAL:
            if not self.factory_instances.get(stream_id):
                stream = marionette_tg.multiplexer.MarionetteStream(
                    self.multiplexer_incoming_, self.multiplexer_outgoing_,
                    stream_id)
                self.factory_instances[stream_id] = self.factory()
                self.factory_instances[stream_id].connectionMade(stream)

            payload = cell_obj.get_payload()
            if payload:
                self.factory_instances[stream_id].dataReceived(payload)
