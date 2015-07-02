import sys

sys.path.append('.')

import marionette_tg.channel
import marionette_tg.dsl

EVENT_LOOP_FREQUENCY_S = 0.001

class Executable(object):

    def __init__(self, party, format, multiplexer_outgoing, multiplexer_incoming):
        self.party_ = party
        self.format_ = format
        self.port_ = None
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.multiplexer_incoming_ = multiplexer_incoming
        self.executables_ = self.load(party, format)

    def load(self, party, format):
        executables = marionette_tg.dsl.load_all(party, format)

        for executable in executables:
            executable.set_multiplexer_outgoing(self.multiplexer_outgoing_)
            executable.set_multiplexer_incoming(self.multiplexer_incoming_)

        return executables

    def execute(self, reactor):
        for executable in self.executables_:
            reactor.callFromThread(executable.execute, reactor)
        reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def isRunning(self):
        retval = False
        for executable in self.executables_:
            if executable.isRunning():
                retval = True
                break
        return retval

    def replicate(self):
        retval = Executable(self.party_, self.format_,
                            self.multiplexer_outgoing_,
                            self.multiplexer_incoming_)
        retval.executables_ = [executable.replicate()
                                for executable
                                  in self.executables_]
        return retval

    def stop(self):
        for executable in self.executables_:
            executable.stop()

    def check_for_incoming_connections(self):
        retval = None

        if self.party_ == "server":
            channel = marionette_tg.channel.accept_new_channel(self.get_port())
            if channel:
                retval = self.replicate()
                retval.set_channel(channel)

        return retval

    def get_port(self):
        ports = []
        for executable in self.executables_:
            ports += [executable.get_port()]
        assert len(ports)>0
        assert all(p == ports[0] for p in ports)

        return ports[0]

    def set_global(self, key, value):
        for executable in self.executables_:
            executable.set_global(key, value)

    def set_local(self, key, value):
        for executable in self.executables_:
            executable.set_local(key, value)

    def set_channel(self, channel):
        for executable in self.executables_:
            executable.set_channel(channel)