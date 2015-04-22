#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string

class MarionetteAction(object):
    def __init__(self, action_name, party, to_do):
        self.action_name_ = action_name
        self.party_ = party
        self.to_do_ = to_do

    def execute(self, party, action_name):
        retval = None

        if self.party_ == party \
            and (self.action_name_ == action_name):
            retval = self.to_do_

        return retval

    def get_module(self):
        module = self.to_do_.partition(".")[0]
        return module

    def get_method(self):
        method = self.to_do_.partition(".")[2].partition("(")[0]
        return method

    def get_args(self):
        args_str = self.to_do_.partition(".")[2].partition("(")[2][:-1]
        args_tmp = args_str.split(', ')
        args = []
        for arg in args_tmp:
            if len(arg) > 0 and arg[0] == "\"" and arg[-1] == "\"":
                args.append(arg[1:-1])
            else:
                args.append(arg)
        return args