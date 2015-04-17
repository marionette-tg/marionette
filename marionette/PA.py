#0!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import random
import importlib
import threading

import regex2dfa
import fte.encoder
import fte.bit_ops


class PA(threading.Thread):
    def __init__(self, party, first_sender):
        super(PA, self).__init__()

        self.states_ = {}
        self.actions_ = []
        self.global_args_ = {}
        self.local_args_ = {}
        self.actions_to_execute_ = {}
        self.first_sender_ = first_sender

        self.local_args_["party"] = party

        if first_sender == self.local_args_["party"]:
            self.local_args_["model_instance_id"] = fte.bit_ops.bytes_to_long(
                os.urandom(4))
            self.local_args_["rng"] = random.Random()
            self.local_args_["rng"].seed(self.local_args_["model_instance_id"])
        else:
            self.local_args_["model_instance_id"] = None
            self.local_args_["rng"] = None

        self.local_args_["last_state"] = None
        self.local_args_["current_state"] = "start"
        self.local_args_["next_state"] = None
        self.local_args_["state_history"] = []
        #self.local_args_["sequence_id"] = 0
        #traceback.print_stack()

        self.multiplexer_outgoing_ = None
        self.multiplexer_incoming_ = None
        self.port_ = None
        self.transport_ = None
        self.channel_ = None

        self.running_ = threading.Event()

    def run(self):
        self.running_.set()
        while self.running_.is_set() and self.isRunning():
            self.transition()

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
                if not self.global_args_.get(fte_key):
                    dfa = regex2dfa.regex2dfa(regex)
                    self.global_args_[fte_key] = fte.encoder.DfaEncoder(
                        dfa, msg_len)

            # load plugin
            action_key = 'action_key-' + action.to_do_
            if not self.global_args_.get(action_key):
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
                i = importlib.import_module("marionette.plugins." + module)
                self.global_args_[action_key] = [getattr(i, function), args]

        for src_state in self.states_:
            for dst_state in self.states_[src_state].transitions_:
                if not self.global_args_.get(
                    'ate-' + src_state + '-' + dst_state):
                    actions_to_execute = []
                    for action in self.actions_:
                        action_name = self.states_[src_state].transitions_[dst_state][0]
                        retval = action.execute(self.local_args_["party"],
                                                action_name)
                        if retval is not None:
                            actions_to_execute.append(retval)
                    self.global_args_['ate-' + src_state + '-' +
                                      dst_state] = actions_to_execute

    def transition(self):
        retval = False

        if not self.local_args_.get("rng") and self.local_args_.get(
            "model_instance_id"):
            self.local_args_["rng"] = random.Random()
            self.local_args_["rng"].seed(self.local_args_["model_instance_id"])
            transitions = len(self.local_args_["state_history"])

            self.local_args_["state_history"] = []
            self.local_args_["current_state"] = 'start'
            for i in range(transitions):
                self.local_args_["state_history"].append(
                    self.local_args_["current_state"])
                self.local_args_["current_state"] = self.states_[self.local_args_["current_state"]].transition(
                    self.local_args_.get("rng"))
            self.local_args_["next_state"] = None

        src_state = self.local_args_["current_state"]

        if self.local_args_.get("rng"):
            if not self.local_args_["next_state"]:
                self.local_args_["next_state"] = self.states_[src_state].transition(
                    self.local_args_.get("rng"))
            potential_transitions = [self.local_args_["next_state"]]
        else:
            potential_transitions = list(self.states_[src_state].transitions_.keys())

        for dst_state in potential_transitions:
            actions_to_execute = self.global_args_['ate-' + src_state + '-' +
                                                   dst_state]

            success = True
            for action in actions_to_execute:
                action_retval = self.eval_action(action, self.channel_)
                if not action_retval:
                    success = False
                    break

            if success:
                self.local_args_["current_state"] = dst_state
                self.local_args_["state_history"].append(src_state)
                self.local_args_["next_state"] = None
                retval = True
                break

        return retval

    def replicate(self):
        retval = PA(self.local_args_["party"], self.first_sender_)
        retval.actions_ = self.actions_
        retval.states_ = self.states_
        retval.global_args_ = self.global_args_
        retval.local_args_["model_uuid"] = self.local_args_["model_uuid"]
        retval.multiplexer_outgoing_ = self.multiplexer_outgoing_
        retval.multiplexer_incoming_ = self.multiplexer_incoming_
        retval.transport_ = self.transport_
        retval.port_ = self.port_
        return retval

    def isRunning(self):
        return (self.local_args_["current_state"] != "dead")

    def eval_action(self, action, channel):
        action_key = 'action_key-' + action
        [methodToCall, args] = self.global_args_[action_key]

        success = methodToCall(channel, self.global_args_, self.local_args_, args)

        return success

    def getCurrentState(self):
        return self.local_args_["current_state"]

    def add_state(self, name):
        if not name in list(self.states_.keys()):
            self.states_[name] = PAState(name)

    def set_channel(self, channel):
        self.channel_ = channel

    def get_channel(self, ):
        return self.channel_

    def set_multiplexer_outgoing(self, multiplexer):
        self.global_args_["multiplexer_outgoing"] = multiplexer

    def set_multiplexer_incoming(self, multiplexer):
        self.global_args_["multiplexer_incoming"] = multiplexer

    def stop(self):
        self.running_.clear()
        self.local_args_["current_state"] = "dead"

    def get_client_instance_id(self):
        return self.local_args_["model_instance_id"]

    def set_transport(self, transport):
        self.transport_ = transport

    def set_port(self, port):
        self.port_ = port

    def get_transport(self):
        return self.transport_

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
