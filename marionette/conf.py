#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser

def get(key):
    global conf_

    try:
        retval = conf_[key]
    except:
        confparser = ConfigParser.RawConfigParser()
        confparser.read('marionette.conf')

        conf_ = {}
        conf_["general.debug"] = confparser.getboolean("general", "debug")
    finally:
        retval = conf_[key]

    return retval