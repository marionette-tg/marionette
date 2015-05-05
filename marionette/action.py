#!/usr/bin/env python
# -*- coding: utf-8 -*-


class MarionetteAction(object):

    def __init__(self, name, party, module, method, args, regex=None):
        self.name_ = name
        self.party_ = party
        self.module_ = module
        self.method_ = method
        self.args_ = args
        self.regex_match_incoming_ = regex

    def set_name(self, name):
        self.name_ = name

    def get_name(self):
        return self.name_

    def set_party(self, party):
        self.party_ = party

    def get_party(self):
        return self.party_

    def set_module(self, module):
        self.module_ = module

    def get_module(self):
        return self.module_

    def set_method(self, method):
        self.method_ = method

    def get_method(self):
        return self.method_

    def set_args(self, args):
        self.args_ = args

    def get_args(self):
        return self.args_

    def set_regex_match_incoming(self, regex):
        self.regex_match_incoming_ = regex

    def get_regex_match_incoming(self):
        return self.regex_match_incoming_

    def execute(self, party, name):
        retval = None

        if self.party_ == party \
                and (self.name_ == name):
            retval = True

        return retval
