#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import hashlib

import fte.bit_ops

import marionette.action

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


def str_to_settings(mar_str):
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
            party = line.strip().split(' ')[0]
            action_cmd = ' '.join(line.strip().split(' ')[1:])
            action = marionette.action.MarionetteAction(action_name,
                                                        party,
                                                        action_cmd)
            settings.add_action(action)

            if action_cmd.startswith("model"):
                continue

            comp_party = "server" if party=="client" else "client"
            comp_action_cmd = action_cmd
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

    settings.setPort(connection_port)

    return settings

def load(party, format_name):
    with open("marionette/formats/" + format_name + ".mar") as f:
        mar_str = f.read()

    settings = str_to_settings(mar_str)

    first_sender = 'client'
    if format_name in ["ftp_pasv_transfer"]:
        first_sender = "server"

    executable = marionette.PA.PA(party, first_sender)
    executable.set_port(settings.getPort())
    executable.marionette_state_.set_local("model_uuid", get_model_uuid(mar_str))
    for transition in settings.getTransitions():
        executable.add_state(transition[0])
        executable.add_state(transition[1])
        executable.states_[transition[0]].add_transition(transition[1],
                                                         transition[2],
                                                         transition[3])
    executable.actions_ = settings.get_actions()

    if executable.states_.get("end"):
        executable.add_state("dead")
        executable.states_["end"].add_transition("dead", 'NULL', 1)
        executable.states_["dead"].add_transition("dead", 'NULL', 1)

    return executable


def get_model_uuid(format_str):
    m = hashlib.md5()
    m.update(format_str)
    bytes = m.digest()
    return fte.bit_ops.bytes_to_long(bytes[:4])
