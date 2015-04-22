#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import random
import socket
import struct
import importlib
import threading

import regex2dfa
import fte.encoder
import fte.bit_ops

sys.path.append('.')

import marionette.channel
import marionette.conf

SERVER_IFACE = marionette.conf.get("server.listen_iface")
SERVER_TIMEOUT = 0.001


class PA(threading.Thread):
    def __init__(self, party, first_sender):
        super(PA, self).__init__()

        self.states_ = {}
        self.actions_ = []
        self.marionette_state_ = MarionetteSystemState()
        self.actions_to_execute_ = {}
        self.first_sender_ = first_sender

        self.marionette_state_.set_local("party", party)

        if self.marionette_state_.get_local("party") == first_sender:
            self.marionette_state_.set_local("model_instance_id", fte.bit_ops.bytes_to_long(os.urandom(4)))
            self.marionette_state_.set_local("rng", random.Random())
            self.marionette_state_.get_local("rng").seed(self.marionette_state_.get_local("model_instance_id"))

        self.marionette_state_.set_local("current_state", "start")
        self.marionette_state_.set_local("state_history", [])
        self.marionette_state_.set_global("listening_socket", {})

        self.port_ = None
        self.channel_ = None
        self.running_ = threading.Event()

        self.build_cache()

    def run(self):
        self.running_.set()
        while self.running_.is_set() and self.isRunning():
            self.transition()
        self.channel_.close()

    def openNewChannel(self):
        port = self.get_port()
        assert port

        for i in range(10):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((SERVER_IFACE, int(port)))
                channel = marionette.channel.new(s)
            except Exception as e:
                channel = None
            finally:
                if channel: break

        return channel

    def acceptNewChannel(self):
        port = self.get_port()
        assert port

        if not self.marionette_state_.get_global('listening_socket').get(port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                         struct.pack('ii', 0, 0))
            s.bind((SERVER_IFACE, int(port)))
            s.listen(5)
            s.settimeout(SERVER_TIMEOUT)
            self.marionette_state_.get_global('listening_socket')[port] = s

        try:
            conn, addr = self.marionette_state_.get_global('listening_socket')[port].accept()
            channel = marionette.channel.new(conn)
        except socket.timeout:
            channel = None

        return channel

    def build_cache(self):
        # do fte stuff
        for action in self.actions_:
            # precompute FTE
            if action.to_do_.startswith("fte"):
                args_str = action.to_do_.partition(".")[2].partition(
                    "(")[2][:-1]
                args_tmp = args_str.split(', ')
                args = []
                for arg in args_tmp:
                    if len(arg) > 0 and arg[0] == "\"" and arg[-1] == "\"":
                        args.append(arg[1:-1])
                    else:
                        args.append(arg)
                regex = args[0]
                msg_len = int(args[1])
                fte_key = 'fte_key-' + regex + str(msg_len)
                if not self.marionette_state_.get_global(fte_key):
                    dfa = regex2dfa.regex2dfa(regex)
                    self.marionette_state_.set_global(fte_key, fte.encoder.DfaEncoder(dfa, msg_len))

            # load plugin
            action_key = 'action_key-' + action.to_do_
            if not self.marionette_state_.get_global(action_key):
                module = action.to_do_.partition(".")[0]
                function = action.to_do_.partition(".")[2].partition("(")[0]
                args_str = action.to_do_.partition(".")[2].partition(
                    "(")[2][:-1]
                args_tmp = args_str.split(', ')
                args = []
                for arg in args_tmp:
                    if len(arg) > 0 and arg[0] == "\"" and arg[-1] == "\"":
                        args.append(arg[1:-1])
                    else:
                        args.append(arg)
                i = importlib.import_module("marionette.plugins._" + module)
                self.marionette_state_.set_global(action_key, [getattr(i, function), args])

        for src_state in self.states_:
            for dst_state in self.states_[src_state].transitions_:
                if not self.marionette_state_.get_global(
                    'ate-' + src_state + '-' + dst_state):
                    actions_to_execute = []
                    for action in self.actions_:
                        action_name = self.states_[src_state].transitions_[dst_state][0]
                        retval = action.execute(self.marionette_state_.get_local("party"),
                                                action_name)
                        if retval is not None:
                            actions_to_execute.append(retval)
                    self.marionette_state_.set_global('ate-' + src_state + '-' + dst_state, actions_to_execute)

    def transition(self):
        retval = False

        if not self.get_channel():
            if self.marionette_state_.get_local("party") == "client":
                channel = self.openNewChannel()
                self.set_channel(channel)

        if not self.marionette_state_.get_local("rng") and self.marionette_state_.get_local("model_instance_id"):
            self.marionette_state_.set_local("rng", random.Random())
            self.marionette_state_.get_local("rng").seed(self.marionette_state_.get_local("model_instance_id"))
            transitions = len(self.marionette_state_.get_local("state_history"))

            self.marionette_state_.set_local("state_history", [])
            self.marionette_state_.set_local("current_state", 'start')
            for i in range(transitions):
                current_state = self.marionette_state_.get_local("current_state")
                rng = self.marionette_state_.get_local("rng")
                self.marionette_state_.get_local("state_history").append(current_state)
                self.marionette_state_.set_local("current_state", self.states_[current_state].transition(rng))
            self.marionette_state_.set_local("next_state", None)

        src_state = self.marionette_state_.get_local("current_state")
        if self.marionette_state_.get_local("rng"):
            if not self.marionette_state_.get_local("next_state"):
                self.marionette_state_.set_local("next_state", self.states_[src_state].transition(self.marionette_state_.get_local("rng")))
            potential_transitions = [self.marionette_state_.get_local("next_state")]
        else:
            potential_transitions = list(self.states_[src_state].transitions_.keys())

        for dst_state in potential_transitions:
            actions_to_execute = self.marionette_state_.get_global('ate-' + src_state + '-' + dst_state)

            success = True
            for action in actions_to_execute:
                action_retval = self.eval_action(action, self.channel_)
                if not action_retval:
                    success = False
                    break

            if success:
                self.marionette_state_.set_local("current_state", dst_state)
                self.marionette_state_.get_local("state_history").append(src_state)
                self.marionette_state_.set_local("next_state", None)
                retval = True
                break

        return retval

    def spawn(self):
        retval = None

        if self.marionette_state_.get_local("party") == "server":
            channel = self.acceptNewChannel()
            if channel:
                retval = self.replicate()
                retval.set_channel(channel)

        return retval


    def replicate(self):
        retval = PA(self.marionette_state_.get_local("party"),
                    self.first_sender_)
        retval.actions_ = self.actions_
        retval.states_ = self.states_
        for key in self.marionette_state_.global_:
            retval.marionette_state_.global_[key] = self.marionette_state_.global_[key]
        retval.marionette_state_.set_local("model_uuid", self.marionette_state_.get_local("model_uuid"))
        retval.port_ = self.port_
        retval.build_cache()
        return retval

    def isRunning(self):
        return (self.marionette_state_.get_local("current_state") != "dead")

    def eval_action(self, action, channel):
        action_key = 'action_key-' + action
        [methodToCall, args] = self.marionette_state_.get_global(action_key)

        success = methodToCall(channel, self.marionette_state_, args)

        return success

    def add_state(self, name):
        if not name in list(self.states_.keys()):
            self.states_[name] = PAState(name)

    def set_channel(self, channel):
        self.channel_ = channel

    def get_channel(self, ):
        return self.channel_

    def set_multiplexer_outgoing(self, multiplexer):
        self.marionette_state_.set_global("multiplexer_outgoing", multiplexer)

    def set_multiplexer_incoming(self, multiplexer):
        self.marionette_state_.set_global("multiplexer_incoming", multiplexer)

    def stop(self):
        self.running_.clear()
        self.marionette_state_.set_local("current_state", "dead")

    def get_client_instance_id(self):
        return self.marionette_state_.get_local("model_instance_id")

    def set_port(self, port):
        self.port_ = port

    def get_port(self):
        return self.port_


class PAState(object):
    def __init__(self, name):
        self.name_ = name
        self.transitions_ = {}
        self.format_type_ = None
        self.format_value_ = None

    def add_transition(self, dst, action_name, probability):
        self.transitions_[dst] = [action_name, float(probability)]

    def transition(self, rng):
        assert (rng or len(self.transitions_) == 1)
        if rng:
            coin = rng.random()
            sum = 0
            for state in self.transitions_:
                sum += self.transitions_[state][1]
                if sum >= coin:
                    break
        else:
            state = list(self.transitions_.keys())[0]
        return state


class MarionetteSystemState(object):
    def __init__(self):
        self.global_ = {}
        self.global_lock_ = threading.RLock()

        self.local_ = {}
        self.local_lock_ = threading.RLock()

    def set_global(self, key, val):
        with self.global_lock_:
            self.global_[key] = val

    def get_global(self, key):
        with self.global_lock_:
            return self.global_.get(key)

    def set_local(self, key, val):
        with self.local_lock_:
            self.local_[key] = val

    def get_local(self, key):
        with self.local_lock_:
            return self.local_.get(key)
