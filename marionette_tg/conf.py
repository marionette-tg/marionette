#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import ConfigParser

def find_conf_file():
    search_dirs = [sys.prefix,
                   '/etc',
                   '.',
                   os.path.dirname(__file__),
                  ]
    for dir in search_dirs:
        conf_path = os.path.join(dir, 'marionette.conf')
        if os.path.exists(conf_path):
            return conf_path
        conf_path = os.path.join(dir, 'marionette_tg', 'marionette.conf')
        if os.path.exists(conf_path):
            return conf_path

    return None

def get(key):
    global conf_

    try:
        retval = conf_[key]
    except:
        confparser = ConfigParser.RawConfigParser()
        conf_file_path = find_conf_file()
        if not conf_file_path:
            raise Exception('can\'t find marionette_tg.conf')
        confparser.read(conf_file_path)

        conf_ = {}
        conf_["general.debug"] = confparser.getboolean("general", "debug")
        conf_["general.autoupdate"] = confparser.getboolean("general", "autoupdate")
        conf_["general.update_server"] = confparser.get("general", "update_server")
        conf_["client.listen_iface"] = confparser.get("client", "listen_iface")
        conf_["client.listen_port"] = confparser.getint(
            "client", "listen_port")
        conf_["server.listen_iface"] = confparser.get("server", "listen_iface")
        conf_["server.proxy_iface"] = confparser.get("server", "proxy_iface")
        conf_["server.proxy_port"] = confparser.getint("server", "proxy_port")
    finally:
        retval = conf_[key]

    return retval
