#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import unittest

sys.path.append(".")

import marionette.driver
import marionette.multiplexer

PERF_DEBUG = False

if PERF_DEBUG: import yappi

CLIENT_MESSAGE = 'x' * 1024 * 256
SERVER_MESSAGE = 'y' * 1024 * 256


def mbps(bytes, seconds):
    bytes_per_second = int(bytes) / float(seconds)
    bit_per_second = bytes_per_second * 8
    megabits_per_second = bit_per_second / (1024**2)
    return megabits_per_second


class Tests(unittest.TestCase):
    def doExperiment(self, format):
        server = marionette.Server(format)
        server.start()

        client = marionette.Client(format)
        client.start()

        client_stream = client.start_new_stream()
        client_stream.push(CLIENT_MESSAGE)

        while len(server.get_streams()) == 0:
            time.sleep(0)

        server_stream = server.get_stream(server.get_streams().keys()[0])
        server_stream.push(SERVER_MESSAGE)

        start = time.time()

        if PERF_DEBUG: yappi.start()
        while True:
            if client_stream \
                    and client_stream.peek() == SERVER_MESSAGE:
                break
            time.sleep(0)
        if PERF_DEBUG: yappi.get_func_stats().print_all()

        seconds = time.time() - start
        bytes = len(SERVER_MESSAGE)

        if PERF_DEBUG: print('\n',[seconds, bytes, mbps(bytes, seconds)])

        while True:
            if server_stream and server_stream.peek() == CLIENT_MESSAGE:
                break
            time.sleep(0)

        client.stop()
        client.join()

        server.stop()
        server.join()

    def test_clientServer_http_simple_blocking(self):
        self.doExperiment("http_simple_blocking")

    def test_clientServer_http_simple_blocking_with_msg_lens(self):
        self.doExperiment("http_simple_blocking_with_msg_lens")

    def test_clientServer_http_simple_nonblocking(self):
        self.doExperiment("http_simple_nonblocking")

    def test_clientServer_http_squid_blocking(self):
        self.doExperiment("http_squid_blocking")

    def test_clientServer_ssh_simple_nonblocking(self):
        self.doExperiment("ssh_simple_nonblocking")

    def test_clientServer_smb_simple_nonblocking(self):
        self.doExperiment("smb_simple_nonblocking")

    #def test_clientServer_pop3_simple_blocking(self):
    #    self.doExperiment("pop3_simple_blocking")

    # def test_clientServer_ftp_simple_blocking(self):
    #     self.doExperiment("ftp_simple_blocking")
    #
    # def test_clientServer_http_simple_blocking(self):
    #     self.doExperiment("amazon_simple")
    #
    # def test_clientServer_http_simple_blocking(self):
    #     self.doExperiment("amazon_connection")


if __name__ == '__main__':
    unittest.main()