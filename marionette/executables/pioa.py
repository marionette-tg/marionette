#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import random
import importlib

from twisted.python import log

sys.path.append('.')

import fte
import fte.encoder
import fte.bit_ops

import marionette.channel

EVENT_LOOP_FREQUENCY_S = 0.001

# the following varibles are reserved and shouldn't be passed down
#   to spawned models.
RESERVED_LOCAL_VARS = ['party','model_instance_id','model_uuid']

class PIOA(object):

    def __init__(self, party, first_sender):
        super(PIOA, self).__init__()

        self.actions_ = []
        self.channel_ = None
        self.channel_requested_ = False
        self.current_state_ = 'start'
        self.first_sender_ = first_sender
        self.next_state_ = None
        self.marionette_state_ = MarionetteSystemState()
        self.marionette_state_.set_local("party", party)
        self.party_ = party
        self.port_ = None
        self.transport_protocol_ = None
        self.rng_ = None
        self.history_len_ = 0
        self.states_ = {}
        self.success_ = False

        if self.party_ == first_sender:
            self.marionette_state_.set_local(
                "model_instance_id", fte.bit_ops.bytes_to_long(os.urandom(4)))
            self.rng_ = random.Random()
            self.rng_.seed(
                self.marionette_state_.get_local("model_instance_id"))

    def do_precomputations(self):
        for action in self.actions_:
            if action.get_module() == 'fte' and action.get_method().startswith('send'):
                [regex, msg_len] = action.get_args()
                self.marionette_state_.get_fte_obj(regex, msg_len)

    def execute(self, reactor):
        if self.isRunning():
            self.transition()
            reactor.callLater(EVENT_LOOP_FREQUENCY_S, self.execute, reactor)
        else:
            self.channel_.close()


    def check_channel_state(self):
        if self.party_ == "client":
            if not self.channel_:
                if not self.channel_requested_:
                    marionette.channel.open_new_channel(self.get_transport_protocol(), 
                        self.get_port(), self.set_channel)
                    self.channel_requested_ = True
        return (self.channel_ != None)

    def set_channel(self, channel):
        self.channel_ = channel

    def check_rng_state(self):
        if self.marionette_state_.get_local("model_instance_id"):
            if not self.rng_:
                self.rng_ = random.Random()
                self.rng_.seed(
                    self.marionette_state_.get_local("model_instance_id"))

                self.current_state_ = 'start'
                for i in range(self.history_len_):
                    self.current_state_ = self.states_[
                        self.current_state_].transition(self.rng_)
                self.next_state_ = None

            #Reset history length once RNGs are sync'd
            self.history_len_ = 0

    def determine_action_block(self, src_state, dst_state):
        retval = []
        for action in self.actions_:
            action_name = self.states_[src_state].transitions_[dst_state][0]
            success = action.execute(self.party_, action_name)
            if success is not None:
                retval.append(action)
        return retval

    def get_potential_transitions(self):
        retval = []

        if self.rng_:
            if not self.next_state_:
                self.next_state_ = self.states_[
                    self.current_state_].transition(self.rng_)
            retval += [self.next_state_]
        else:
            for transition in \
                self.states_[self.current_state_].transitions_.keys():
                if self.states_[self.current_state_].transitions_[transition][1]>0:
                    retval += [transition]

        return retval

    def advance_to_next_state(self):
        retval = False

        # get the list of possible transitions we could make
        potential_transitions = self.get_potential_transitions()
        assert len(potential_transitions) > 0

        # attempt to do a normal transition
        fatal = 0
        success = False
        for dst_state in potential_transitions:
            action_block = self.determine_action_block(self.current_state_, dst_state)

            try:
                success = self.eval_action_block(action_block)
            except Exception as e:
                log.msg("EXCEPTION: %s" % (str(e)))
                fatal += 1
            finally:
                if success:
                    break

        # if all potential transitions are fatal, attempt the error transition
        if not success and fatal == len(potential_transitions):
            src_state = self.current_state_
            dst_state = self.states_[self.current_state_].get_error_transition()

            if dst_state:
                action_block = self.determine_action_block(src_state, dst_state)
                success = self.eval_action_block(action_block)

        # if we have a successful transition, update our state info.
        if success:
            self.history_len_ += 1
            self.current_state_ = dst_state
            self.next_state_ = None
            retval = True

            if self.current_state_ == 'dead':
                self.success_ = True

        return retval

    def eval_action_block(self, action_block):
        retval = False

        if len(action_block)==0:
            retval = True
        elif len(action_block)>=1:
            for action_obj in action_block:
                if action_obj.get_regex_match_incoming():
                    incoming_buffer = self.channel_.peek()
                    m = re.search(action_obj.get_regex_match_incoming(), incoming_buffer)
                    if m:
                        retval = self.eval_action(action_obj)
                else:
                    retval = self.eval_action(action_obj)
                if retval: break

        return retval

    def transition(self):
        success = False
        if self.check_channel_state():
            self.check_rng_state()
            success = self.advance_to_next_state()
        return success

    def replicate(self):
        retval = PIOA(self.party_,
                    self.first_sender_)
        retval.actions_ = self.actions_
        retval.states_ = self.states_
        retval.marionette_state_.global_ = self.marionette_state_.global_
        model_uuid = self.marionette_state_.get_local("model_uuid")
        retval.marionette_state_.set_local("model_uuid", model_uuid)
        retval.port_ = self.port_
        retval.transport_protocol_ = self.transport_protocol_
        return retval

    def isRunning(self):
        return (self.current_state_ != "dead")

    def eval_action(self, action_obj):
        module = action_obj.get_module()
        method = action_obj.get_method()
        args = action_obj.get_args()

        i = importlib.import_module("marionette.plugins._" + module)
        method_obj = getattr(i, method)

        success = method_obj(self.channel_, self.marionette_state_, args)

        return success

    def add_state(self, name):
        if not name in list(self.states_.keys()):
            self.states_[name] = PAState(name)

    def set_multiplexer_outgoing(self, multiplexer):
        self.marionette_state_.set_global("multiplexer_outgoing", multiplexer)

    def set_multiplexer_incoming(self, multiplexer):
        self.marionette_state_.set_global("multiplexer_incoming", multiplexer)

    def stop(self):
        self.current_state_ = "dead"

    def set_port(self, port):
        self.port_ = port

    def get_port(self):
        retval = None

        try:
            retval = int(self.port_)
        except ValueError:
            retval = self.marionette_state_.get_local(self.port_)

        return retval
    def set_transport_protocol(self, transport_protocol):
        self.transport_protocol_ = transport_protocol

    def get_transport_protocol(self):
        return self.transport_protocol_

    def set_local(self, key, value):
        self.marionette_state_.set_local(key, value)

    def set_global(self, key, value):
        self.marionette_state_.set_global(key, value)

    def get_local(self, key):
        return self.marionette_state_.get_local(key)

    def get_global(self, key):
        return self.marionette_state_.get_global(key)

    def get_success(self):
        return self.success_

class PAState(object):

    def __init__(self, name):
        self.name_ = name
        self.transitions_ = {}
        self.format_type_ = None
        self.format_value_ = None
        self.error_state_ = None

    def add_transition(self, dst, action_name, probability):
        self.transitions_[dst] = [action_name, float(probability)]

    def set_error_transition(self, error_state):
        self.error_state_ = error_state

    def get_error_transition(self):
        return self.error_state_

    def transition(self, rng):
        assert (rng or len(self.transitions_) == 1)
        if rng and len(self.transitions_) > 1:
            coin = rng.random()
            sum = 0
            for state in self.transitions_:
                if self.transitions_[state][1] == 0:
                    continue
                sum += self.transitions_[state][1]
                if sum >= coin:
                    break
        else:
            state = list(self.transitions_.keys())[0]
        return state


class MarionetteSystemState(object):

    def __init__(self):
        self.global_ = {}
        self.local_ = {}

    def set_global(self, key, val):
        self.global_[key] = val

    def get_global(self, key):
        return self.global_.get(key)

    def set_local(self, key, val):
        self.local_[key] = val

    def get_local(self, key):
        return self.local_.get(key)

    def get_fte_obj(self, regex, msg_len):
        fte_key = 'fte_obj-' + regex + str(msg_len)
        if not self.get_global(fte_key):
            dfa = fte.regex2dfa.regex2dfa(regex)
            fte_obj = fte.encoder.DfaEncoder(dfa, msg_len)
            self.set_global(fte_key, fte_obj)

        return self.get_global(fte_key)
