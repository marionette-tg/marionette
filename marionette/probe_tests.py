#!/usr/bin/env python
# coding: utf-8

import os
import sys
import time
import httplib
import unittest
import threading

sys.path.append('.')

import marionette.conf


def execute(cmd):
    os.system(cmd)


class Tests(unittest.TestCase):

    def startservers(self, format):
        server_proxy_iface = marionette.conf.get("server.proxy_iface")

        execute("./bin/marionette_server %s 18081 %s &" %
                (server_proxy_iface, format))
        time.sleep(0.25)

    def stopservers(self):
        execute("pkill -9 -f marionette_server")

    def do_probe(self):
        server_listen_iface = marionette.conf.get("server.listen_iface")
        conn = httplib.HTTPConnection(
            server_listen_iface, 8080, False, timeout=10)
        conn.request("GET", "/")
        response = conn.getresponse()
        actual_response = response.read()
        conn.close()

        expected_response = 'Hello World!'

        self.assertEqual(actual_response, expected_response)

    def test_active_probing(self):
            try:
                format = "http_active_probing"
                self.startservers(format)
                self.do_probe()
            finally:
                self.stopservers()

if __name__ == '__main__':
    unittest.main()
