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
        conf_["client.listen_iface"] = confparser.get("client", "listen_iface")
        conf_["client.listen_port"] = confparser.getint("client", "listen_port")
        conf_["server.listen_iface"] = confparser.get("server", "listen_iface")
        conf_["server.proxy_iface"] = confparser.get("server", "proxy_iface")
        conf_["server.proxy_port"] = confparser.getint("server", "proxy_port")
    finally:
        retval = conf_[key]

    return retval