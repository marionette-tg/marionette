#!/usr/bin/env python
# -*- coding: utf-8 -*-

import marionette.action
import marionette.channel
import marionette.conf
import marionette.executable

class ClientDriver(object):

    def __init__(self, party):
        self.party_ = party

        self.to_start_ = []
        self.running_ = []

        self.executeable_ = None
        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None
        self.state_ = None

    def execute(self, reactor):
        while len(self.to_start_) > 0:
            executable = self.to_start_.pop()
            self.running_.append(executable)

            if self.state_:
                for key in self.state_.local_:
                    if key not in marionette.executables.pioa.RESERVED_LOCAL_VARS:
                        executable.set_local(key, self.state_.local_[key])

            reactor.callFromThread(executable.execute, reactor)

        self.running_ = [executable for executable
                         in self.running_
                         if executable.isRunning()]

    def isRunning(self):
        return len(self.running_ + self.to_start_) > 0

    def setFormat(self, format_name, format_version=None):
        self.executeable_ = marionette.executable.Executable(self.party_, format_name,
                                                         format_version,
                                                         self.multiplexer_outgoing_,
                                                         self.multiplexer_incoming_)
        self.reset()

    def set_multiplexer_outgoing(self, multiplexer):
        self.multiplexer_outgoing_ = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.multiplexer_incoming_ = multiplexer

    def reset(self, n=1):
        self.to_start_ = []
        for i in range(n):
            self.to_start_ += [self.executeable_.replicate()]

    def set_state(self, state):
        self.state_ = state

    def stop(self):
        for executable in self.running_:
            executable.stop()
        for executable in self.to_start_:
            executable.stop()
        self.running_ = []
        self.to_start_ = []

class ServerDriver(object):

    def __init__(self, party):
        self.party_ = party

        self.running_ = []

        self.num_executables_completed_ = 0

        self.executable_ = None
        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None
        self.state_ = None

    def execute(self, reactor):
        while True:
            new_executable = self.executable_.check_for_incoming_connections()
            if new_executable is None:
                break

            self.running_.append(new_executable)
            reactor.callFromThread(new_executable.execute, reactor)

        running_count = len(self.running_)
        self.running_ = [executable for executable
                         in self.running_
                         if executable.isRunning()]

        self.num_executables_completed_ += (running_count - len(self.running_))

    def isRunning(self):
        return len(self.running_)

    def setFormat(self, format_name, format_version=None):
        self.executable_ = marionette.executable.Executable(self.party_, format_name,
                                                         format_version,
                                                         self.multiplexer_outgoing_,
                                                         self.multiplexer_incoming_)

    def set_multiplexer_outgoing(self, multiplexer):
        self.multiplexer_outgoing_ = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.multiplexer_incoming_ = multiplexer

    def set_state(self, state):
        self.state_ = state

        if self.state_:
            for key in self.state_.local_:
                if key not in marionette.executables.pioa.RESERVED_LOCAL_VARS:
                    self.executable_.set_local(key, self.state_.local_[key])

    def stop(self):
        self.executable_.stop()
