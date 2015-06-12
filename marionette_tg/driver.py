#!/usr/bin/env python
# -*- coding: utf-8 -*-

import marionette_tg.action
import marionette_tg.channel
import marionette_tg.conf
import marionette_tg.dsl
import marionette_tg.PA


class ClientDriver(object):

    def __init__(self, party):
        self.party_ = party

        self.to_start_ = []
        self.running_ = []

        self.executeable_ = None
        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None

    def execute(self, reactor):
        while len(self.to_start_) > 0:
            executable = self.to_start_.pop()
            self.running_.append(executable)
            reactor.callFromThread(executable.execute, reactor)

        self.running_ = [executable for executable
                         in self.running_
                         if executable.isRunning()]

    def isRunning(self):
        return len(self.running_ + self.to_start_) > 0

    def setFormat(self, format_name):
        executable = marionette_tg.dsl.load(self.party_, format_name)
        executable.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        executable.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.executeable_ = executable
        self.reset()

    def set_multiplexer_outgoing(self, multiplexer):
        self.multiplexer_outgoing_ = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.multiplexer_incoming_ = multiplexer

    def reset(self, n=1):
        self.to_start_ = []
        for i in range(n):
            self.to_start_ += [self.executeable_.replicate()]


class ServerDriver(object):

    def __init__(self, party):
        self.party_ = party

        self.running_ = []

        self.num_executables_completed_ = 0

        self.executable_ = None
        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None

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

    def setFormat(self, format_name):
        executable = marionette_tg.dsl.load(self.party_, format_name)
        executable.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        executable.set_multiplexer_incoming(self.multiplexer_incoming_)
        self.executable_ = executable

    def set_multiplexer_outgoing(self, multiplexer):
        self.multiplexer_outgoing_ = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.multiplexer_incoming_ = multiplexer
