import sys

sys.path.append('.')

import marionette.channel
import marionette.dsl

EVENT_LOOP_FREQUENCY_S = 0.001

class Executable(object):

    def __init__(self, party, format_name, format_version, multiplexer_outgoing, multiplexer_incoming):
        self.party_ = party
        self.format_ = format_name
        self.format_version_ = format_version
        self.port_ = None
        self.multiplexer_outgoing_ = multiplexer_outgoing
        self.multiplexer_incoming_ = multiplexer_incoming
        self.executables_ = self.load(party, self.format_, self.format_version_)

    def load(self, party, format_name, format_version):
        executables = marionette.dsl.load_all(party, format_name, format_version)

        executables_tmp = {}
        for executable in executables:
            key = executable.get_local('model_uuid')
            executables_tmp[key] = executable

        executables = []
        for key in executables_tmp.keys():
            executables.append(executables_tmp[key])

        for executable in executables:
            executable.set_multiplexer_outgoing(self.multiplexer_outgoing_)
            executable.set_multiplexer_incoming(self.multiplexer_incoming_)

        return executables

    def execute(self, reactor):
        for executable in self.executables_:
            if executable.get_success():
                for executable in self.executables_:
                    executable.stop()

        if self.isRunning():
            for executable in self.executables_:
                if executable.isRunning():
                    reactor.callFromThread(executable.execute, reactor)

            reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)

    def isRunning(self):
        retval = True
        for executable in self.executables_:
            if executable.get_success():
                retval = False
                break
        return retval

    def replicate(self):
        retval = Executable(self.party_, self.format_, self.format_version_,
                            self.multiplexer_outgoing_,
                            self.multiplexer_incoming_)
        retval.executables_ = [executable.replicate()
                                for executable
                                  in self.executables_]
        return retval

    def stop(self):
        for executable in self.executables_:
            executable.stop()
        if self.party_ == "server":
            marionette.channel.stop_accepting_new_channels(self.get_transport_protocol(), self.get_port())

    def check_for_incoming_connections(self):
        retval = None

        if self.party_ == "server":
            channel = marionette.channel.accept_new_channel(self.get_transport_protocol(), self.get_port())
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

    def get_transport_protocol(self):
        transport_protocols = []
        for executable in self.executables_:
            transport_protocols += [executable.get_transport_protocol()]
        assert len(transport_protocols)>0
        assert all(tp == transport_protocols[0] for tp in transport_protocols)

        return transport_protocols[0]


    def set_global(self, key, value):
        for executable in self.executables_:
            executable.set_global(key, value)

    def set_local(self, key, value):
        for executable in self.executables_:
            executable.set_local(key, value)

    def set_channel(self, channel):
        for executable in self.executables_:
            executable.set_channel(channel)
