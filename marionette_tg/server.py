#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
sys.path.append('.')

from twisted.internet import reactor

from . import driver
from . import multiplexer
from . import record_layer
from . import updater
from . import conf

EVENT_LOOP_FREQUENCY_S = 0.01
AUTOUPDATE_DELAY = 5


class Server(object):
    factory = None

    def __init__(self, format_name):
        self.multiplexer_outgoing_ = multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_cell)

        self.factory_instances = {}

        if self.check_for_update():
            self.do_update()

        self.set_driver(format_name)
        self.reload_ = False

    def set_driver(self, format_name):
        self.format_name_ = format_name
        self.driver_ = driver.ServerDriver("server")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_)

    def execute(self, reactor):
        if not self.driver_.isRunning():
            if self.reload_:
                self.set_driver(self.format_name_)
                self.reload_ = False

        self.driver_.execute(reactor)
        reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def process_cell(self, cell_obj):
        cell_type = cell_obj.get_cell_type()
        stream_id = cell_obj.get_stream_id()

        if cell_type == record_layer.END_OF_STREAM:
            self.factory_instances[stream_id].connectionLost()
            del self.factory_instances[stream_id]
        elif cell_type == record_layer.NORMAL:
            if not self.factory_instances.get(stream_id):
                stream = multiplexer.MarionetteStream(
                    self.multiplexer_incoming_, self.multiplexer_outgoing_,
                    stream_id)
                self.factory_instances[stream_id] = self.factory()
                self.factory_instances[stream_id].connectionMade(stream)

            payload = cell_obj.get_payload()
            if payload:
                self.factory_instances[stream_id].dataReceived(payload)

    # call this function if you want reload formats from disk
    # at the next possible time
    def reload_driver(self):
        self.reload_ = True

    def check_for_update(self):
        # uncomment the following line to check for updates every N seconds
        # instead of just on startup
        # reactor.callLater(N, self.check_for_update, reactor)

        if conf.get("general.autoupdate"):
            self.do_update(self.reload_driver)

    def do_update(self, callback):
        # could be replaced with code that updates from a different
        # source (e.g., local computations)

        update_server = conf.get("general.update_server")
        updater = updater.FormatUpdater(update_server, use_marionette=False, callback=callback)
        return updater.do_update()
