#!/usr/bin/env python
# coding: utf-8

import os
import sys
import time
import httplib
import unittest

sys.path.append('.')

import marionette_tg.conf


def execute(cmd):
    os.system(cmd)


class Tests(unittest.TestCase):

    def startservers(self, format):
        server_proxy_ip = marionette_tg.conf.get("server.proxy_ip")

        execute("./bin/marionette_server --proxy_ip %s --proxy_port 18081 --format %s &" %
                (server_proxy_ip, format))
        time.sleep(5)

    def stopservers(self):
        execute("pkill -9 -f marionette_server")

    def do_probe(self, request_method, request_uri, expected_response):
        server_listen_ip = marionette_tg.conf.get("server.server_ip")
        conn = httplib.HTTPConnection(
            server_listen_ip, 8080, False, timeout=30)
        conn.request(request_method, request_uri)
        response = conn.getresponse()
        actual_response = response.read()
        conn.close()

        self.assertEqual(actual_response, expected_response)

    def test_active_probing1(self):
            try:
                self.startservers("http_active_probing")
                self.do_probe("GET", "/", "Hello, World!")
            finally:
                self.stopservers()

    def test_active_probing2(self):
            try:
                self.startservers("http_active_probing2")
                self.do_probe("GET", "/",         "Hello, World!")
                self.do_probe("GET", "/notfound", "File not found!")
                self.do_probe("ABC", "DEF",       "Bad request!")
            finally:
                self.stopservers()

if __name__ == '__main__':
    unittest.main()
