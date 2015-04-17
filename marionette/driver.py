#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import socket
import struct
import string
import time

import fte.bit_ops

import marionette.PA
import marionette.channel
import marionette.action


SERVER_IFACE = '127.0.0.1'
SERVER_TIMEOUT = 0.001


class MarionetteSettings(object):
    def __init__(self):
        self.transport_ = None
        self.port_ = None
        self.transitions_ = []
        self.actions_ = []

    def setTransport(self, transport):
        self.transport_ = transport

    def getTransport(self):
        return self.transport_

    def setPort(self, port):
        self.port_ = port

    def getPort(self):
        return self.port_

    def setTransition(self, src_state, dst_state, action, probability):
        self.transitions_.append([src_state, dst_state, action, probability])

    def getTransitions(self):
        return self.transitions_

    def add_setup_action(self, action):
        self.actions_.insert(0, action)

    def add_action(self, action):
        self.actions_.append(action)

    def add_teardown_action(self, action):
        self.actions_.append(action)

    def get_actions(self):
        return self.actions_


def parseMarionetteFormat(mar_str):
    settings = MarionetteSettings()
    connection_type = None
    connection_port = None
    mode = ""

    for line in mar_str.split("\n"):
        if line.strip() == "":
            continue

        ###
        line = line.strip()
        while '  ' in line:
            line = string.replace(line,'  ', ' ')
        while '\t\t' in line:
            line = string.replace(line,'\t\t', '\t')
        ###

        # switch mode
        if line.strip().startswith("action"):
            mode = "action"
            action_name = line.strip()[7:-1]
            continue
        if line.strip().startswith("connection"):
            mode = "connection"
            if "(" in line:
                connection_type = line.strip()[11:-2].split(',')[0].strip()
                connection_port = line.strip()[11:-2].split(',')[1].strip()
            continue

        # do action
        if mode == "connection":
            settings.setTransition(line.strip().split(' ')[0],
                                   line.strip().split(' ')[1],
                                   line.strip().split(' ')[2],
                                   line.strip().split(' ')[3])
        if mode == "action":
            action = marionette.action.MarionetteAction(action_name,
                                      line.strip().split(' ')[0],
                                      ' '.join(line.strip().split(' ')[1:]))
            settings.add_action(action)

            # add complementatry action
            party = line.strip().split(' ')[0]
            action_cmd = ' '.join(line.strip().split(' ')[1:])
            comp_party = "server" if party=="client" else "client"

            if action_cmd.startswith("module"):
                action = marionette.action.MarionetteAction(action_name,
                                                            comp_party,
                                                            action_cmd)
                settings.add_action(action)
                continue

            comp_action_cmd = ''
            for module in ['ftem', 'tg']:
                if module+".send" in action_cmd:
                    comp_action_cmd = string.replace(action_cmd,
                                                     module+".send",
                                                     module+".recv")
            for module in ['io']:
                if module+".puts" in action_cmd:
                    comp_action_cmd = string.replace(action_cmd,
                                                     module+".puts",
                                                     module+".gets")

            action = marionette.action.MarionetteAction(action_name,
                                                        comp_party,
                                                        comp_action_cmd)
            settings.add_action(action)


    settings.setTransport(connection_type)
    settings.setPort(connection_port)

    return settings


class Driver(object):
    def __init__(self, party):
        self.clean_executeables_ = []
        self.executeables_ = []
        self.party_ = party
        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None
        self.tcp_socket_map_ = {}

    def execute(self):
        if self.party_ == "server":
            for executable in self.clean_executeables_:
                channel = self.acceptNewChannel(executable)
                if channel:
                    new_executable = executable.replicate()
                    new_executable.set_channel(channel)
                    self.executeables_.append(new_executable)
                    new_executable.start()
        elif self.party_ == "client":
            for executable in self.executeables_:
                if not executable.get_channel():
                    channel = self.openNewChannel(executable)
                    executable.set_channel(channel)
                    executable.start()

        executables_ = []
        for executable in self.executeables_:
            if executable.isRunning():
                executables_.append(executable)
            else:
                channel = executable.get_channel()
                if channel:
                    channel.close()
        self.executeables_ = executables_

    def one_execution_cycle(self, n=1):
        not_opened = []
        self.executeables_ = []
        for executable in self.clean_executeables_:
            for i in range(n):
                new_executable = executable.replicate()
                self.executeables_ += [new_executable]
                not_opened += [new_executable]

        while len(self.executeables_) > 0:
            ###
            if self.party_ == "server":
                if len(not_opened):
                    executable = not_opened[0]
                    channel = self.acceptNewChannel(executable)
                    if channel:
                        executable.set_channel(channel)
                        not_opened.pop(0)
                        executable.start()
            elif self.party_ == "client":
                if len(not_opened):
                    executable = not_opened[0]
                    channel = self.openNewChannel(executable)
                    if channel:
                        executable.set_channel(channel)
                        not_opened.pop(0)
                        executable.start()
                ###

            executables_ = []
            for executable in self.executeables_:
                if executable.isRunning():
                    executables_.append(executable)
                else:
                    channel = executable.get_channel()
                    channel.close()
            self.executeables_ = executables_

    def acceptNewChannel(self, executable):
        port = executable.get_port()

        if not port: return None

        if not self.tcp_socket_map_.get(port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                         struct.pack('ii', 0, 0))
            s.bind((SERVER_IFACE, int(port)))
            s.listen(5)
            s.settimeout(SERVER_TIMEOUT)
            self.tcp_socket_map_[port] = s

        try:
            conn, addr = self.tcp_socket_map_[port].accept()
            channel = marionette.channel.new(conn)
        except socket.timeout:
            channel = None

        return channel

    def openNewChannel(self, executable):
        port = executable.get_port()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IFACE, int(port)))
            channel = marionette.channel.new(s)
        except Exception as e:
            channel = None

        return channel

    def stop(self):
        while len(self.executeables_) > 0:
            executable = self.executeables_.pop(0)
            executable.stop()

    def isRunning(self):
        return len(self.executeables_) > 0

    def setFormat(self, format_name):
        with open("marionette/formats/" + format_name + ".mar") as f:
            mar_str = f.read()

        settings = parseMarionetteFormat(mar_str)

        first_sender = 'client'
        if format_name in ["http_probabilistic_blocking_server_first",
                           "ftp_pasv_transfer_get"]:
            first_sender = "server"

        executable = marionette.PA.PA(self.party_, first_sender)
        executable.set_transport(settings.getTransport())
        executable.set_port(settings.getPort())
        executable.local_args_["model_uuid"] = get_model_uuid(mar_str)
        for transition in settings.getTransitions():
            executable.add_state(transition[0])
            executable.add_state(transition[1])
            executable.states_[transition[0]].add_transition(transition[1],
                                                             transition[2],
                                                             transition[3])
        executable.actions_ = settings.get_actions()
        executable.set_multiplexer_outgoing(self.multiplexer_outgoing_)
        executable.set_multiplexer_incoming(self.multiplexer_incoming_)

        if executable.states_.get("end"):
            executable.add_state("dead")
            executable.states_["end"].add_transition("dead", 'NULL', 1)
            executable.states_["dead"].add_transition("dead", 'NULL', 1)

        executable.build_cache()

        self.clean_executeables_ += [executable]
        if self.party_ == "client":
            self.executeables_ += [executable.replicate()]

    def set_multiplexer_outgoing(self, multiplexer):
        self.multiplexer_outgoing_ = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.multiplexer_incoming_ = multiplexer

    def reset(self):
        self.executeables_ = []
        if self.party_ == "client":
            for executable in self.clean_executeables_:
                self.executeables_ += [executable.replicate()]


def get_model_uuid(format_str):
    m = hashlib.md5()
    m.update(format_str)
    bytes = m.digest()
    return fte.bit_ops.bytes_to_long(bytes[:4])
