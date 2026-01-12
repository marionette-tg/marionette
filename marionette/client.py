#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
import time
sys.path.append('.')

from twisted.internet import reactor
from twisted.python import log

from . import driver
from . import multiplexer
from . import record_layer
from . import updater
from . import dsl
from . import conf

EVENT_LOOP_FREQUENCY_S = 0.01
AUTOUPDATE_DELAY = 5
CLEANUP_INTERVAL_S = 60  # Run cleanup every 60 seconds


class Client(object):

    def __init__(self, format_name, format_version):
        self.multiplexer_outgoing_ = multiplexer.BufferOutgoing()
        self.multiplexer_incoming_ = multiplexer.BufferIncoming()
        self.multiplexer_incoming_.addCallback(self.process_cell)
        self.streams_ = {}
        self.stream_last_activity = {}  # Track last activity time for each stream
        self.stream_counter_ = random.randint(1,2**32-1)

        self.set_driver(format_name, format_version)
        self.reload_ = False

        # first update must be
        reactor.callLater(AUTOUPDATE_DELAY, self.check_for_update)
        
        # Schedule periodic cleanup
        reactor.callLater(CLEANUP_INTERVAL_S, self._periodic_cleanup, reactor)

    def set_driver(self, format_name, format_version=None):
        self.format_name_ = format_name
        if format_version == None:
            self.format_version_ = dsl.get_latest_version(
                'client', format_name)
        else:
            self.format_version_ = format_version
        self.driver_ = driver.ClientDriver("client")
        self.driver_.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.driver_.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        self.driver_.setFormat(self.format_name_, self.format_version_)

    def get_format(self):
        retval = str(self.format_name_) + \
                 ':' + \
                 str(self.format_version_)
        return retval

    def execute(self, reactor):
        if self.driver_.isRunning():
            self.driver_.execute(reactor)
        else:
            if self.reload_:
                self.set_driver(self.format_name_)
                self.reload_ = False
            self.driver_.reset()

        reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def process_cell(self, cell_obj):
        payload = cell_obj.get_payload()
        if payload:
            stream_id = cell_obj.get_stream_id()
            # Update last activity time
            self.stream_last_activity[stream_id] = time.time()
            
            try:
                self.streams_[stream_id].srv_queue.put(payload)
            except:
                log.msg("Client.process_cell: Caught KeyError exception for stream_id :%d"
                    % (stream_id))
                return

    def start_new_stream(self, srv_queue=None):
        stream = multiplexer.MarionetteStream(
            self.multiplexer_incoming_,
            self.multiplexer_outgoing_,
            self.stream_counter_,
            srv_queue)
        stream.host = self
        self.streams_[self.stream_counter_] = stream
        self.stream_last_activity[self.stream_counter_] = time.time()
        self.stream_counter_ = random.randint(1,2**32-1)
        return stream

    def terminate(self, stream_id):
        self._cleanup_stream(stream_id)

    def _cleanup_stream(self, stream_id):
        """Clean up stream resources."""
        if stream_id in self.streams_:
            del self.streams_[stream_id]
        if stream_id in self.stream_last_activity:
            del self.stream_last_activity[stream_id]

    def cleanup_orphaned_streams(self):
        """
        Clean up streams that haven't been active recently.
        Uses the same timeout as BufferIncoming.
        Returns the number of streams cleaned up.
        """
        timeout = multiplexer.BufferIncoming.DEFAULT_STREAM_TIMEOUT
        current_time = time.time()
        orphaned_streams = []
        
        for stream_id, last_activity in list(self.stream_last_activity.items()):
            if current_time - last_activity > timeout:
                orphaned_streams.append(stream_id)
        
        for stream_id in orphaned_streams:
            log.msg("Cleaning up orphaned stream %d (inactive for %.1f seconds)" %
                   (stream_id, current_time - self.stream_last_activity.get(stream_id, 0)))
            self._cleanup_stream(stream_id)
        
        return len(orphaned_streams)

    def _periodic_cleanup(self, reactor):
        """Periodic cleanup task."""
        # Clean up orphaned streams in BufferIncoming
        self.multiplexer_incoming_.cleanup_orphaned_streams()
        
        # Clean up orphaned client streams
        self.cleanup_orphaned_streams()
        
        # Schedule next cleanup
        reactor.callLater(CLEANUP_INTERVAL_S, self._periodic_cleanup, reactor)

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
        format_updater = updater.FormatUpdater(update_server, use_marionette=True, callback=callback)
        return format_updater.do_update()
        
