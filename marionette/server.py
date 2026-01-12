#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
import time
sys.path.append('.')

from twisted.internet import reactor

from . import driver
from . import multiplexer
from . import record_layer
from . import updater
from . import conf

EVENT_LOOP_FREQUENCY_S = 0.01
AUTOUPDATE_DELAY = 5
CLEANUP_INTERVAL_S = 60  # Run cleanup every 60 seconds


class Server(object):
    factory = None

    def __init__(self, format_name):
        self.multiplexer_outgoing_ = multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_cell)

        self.factory_instances = {}
        self.factory_last_activity = {}  # Track last activity time for each factory

        if self.check_for_update():
            self.do_update()

        self.set_driver(format_name)
        self.reload_ = False
        
        # Schedule periodic cleanup
        reactor.callLater(CLEANUP_INTERVAL_S, self._periodic_cleanup, reactor)

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
            if stream_id in self.factory_instances:
                self.factory_instances[stream_id].connectionLost()
            self._cleanup_factory(stream_id)
        elif cell_type == record_layer.NORMAL:
            # Update last activity time
            self.factory_last_activity[stream_id] = time.time()
            
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
        format_updater = updater.FormatUpdater(update_server, use_marionette=False, callback=callback)
        return format_updater.do_update()

    def _cleanup_factory(self, stream_id):
        """Clean up factory instance for a stream."""
        if stream_id in self.factory_instances:
            del self.factory_instances[stream_id]
        if stream_id in self.factory_last_activity:
            del self.factory_last_activity[stream_id]

    def cleanup_orphaned_factories(self):
        """
        Clean up factory instances for streams that haven't been active recently.
        Uses the same timeout as BufferIncoming.
        Returns the number of factories cleaned up.
        """
        timeout = multiplexer.BufferIncoming.DEFAULT_STREAM_TIMEOUT
        current_time = time.time()
        orphaned_streams = []
        
        for stream_id, last_activity in list(self.factory_last_activity.items()):
            if current_time - last_activity > timeout:
                orphaned_streams.append(stream_id)
        
        for stream_id in orphaned_streams:
            from twisted.python import log
            log.msg("Cleaning up orphaned factory for stream %d (inactive for %.1f seconds)" %
                   (stream_id, current_time - self.factory_last_activity.get(stream_id, 0)))
            if stream_id in self.factory_instances:
                self.factory_instances[stream_id].connectionLost()
            self._cleanup_factory(stream_id)
        
        return len(orphaned_streams)

    def _periodic_cleanup(self, reactor):
        """Periodic cleanup task."""
        # Clean up orphaned streams in BufferIncoming
        self.multiplexer_incoming_.cleanup_orphaned_streams()
        
        # Clean up orphaned factory instances
        self.cleanup_orphaned_factories()
        
        # Schedule next cleanup
        reactor.callLater(CLEANUP_INTERVAL_S, self._periodic_cleanup, reactor)
