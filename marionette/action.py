#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string

class MarionetteAction(object):
    def __init__(self, action_name, party, to_do):
        self.action_name_ = action_name
        self.party_ = party

        if to_do.startswith("io."):
            self.to_do_ = string.replace(to_do, "\\n", "\n")
        else:
            self.to_do_ = to_do

    def execute(self, party, action_name):
        retval = None

        if self.party_ == party \
            and (self.action_name_ == action_name):
            retval = self.to_do_

        return retval