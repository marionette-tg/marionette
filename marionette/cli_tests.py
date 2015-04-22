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


def exec_download():
    client_listen_iface = marionette.conf.get("client.listen_iface")
    conn = httplib.HTTPConnection(client_listen_iface, 18079, False, timeout=10)
    conn.request("GET", "/")
    response = conn.getresponse()
    actual_response = response.read()
    conn.close()

    expected_response = ''
    for x in range(2**16):
        expected_response += '_'+str(x)

    assert actual_response == expected_response

    return actual_response

class Tests(unittest.TestCase):

    def startservers(self, format):
        client_listen_iface = marionette.conf.get("client.listen_iface")
        server_proxy_iface = marionette.conf.get("server.proxy_iface")

        execute("./bin/httpserver 18081 %s &" % format)
        time.sleep(1)
        execute("./bin/marionette_server %s 18081 %s &" % (server_proxy_iface, format))
        time.sleep(1)
        execute("./bin/marionette_client %s 18079 %s &" % (client_listen_iface, format))
        time.sleep(1)

    def stopservers(self):
        execute("pkill -9 -f marionette_client")
        execute("pkill -9 -f marionette_server")
        execute("pkill -9 -f httpserver")

    def dodownload_serial(self):
        exec_download()

    def dodownload_parallel(self):
        simultaneous = 10
        threads = []
        for j in range(simultaneous):
            t = threading.Thread(target=exec_download)
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def test_cli_curl(self):
        print ''
        for format in [
                'dummy',
                'http_timings',
                'ftp_simple_blocking',
                'http_simple_blocking',
                'http_squid_blocking',
                'http_simple_nonblocking',
                'http_probabilistic_blocking',
                'http_simple_blocking_with_msg_lens',
                'ssh_simple_nonblocking',
                'smb_simple_nonblocking',
                       ]:
            try:
                self.startservers(format)
                self.dodownload_serial()
                self.dodownload_parallel()
                print '\t', format, '...', 'SUCCESS'
            except Exception as e:
                print '\t', format, '...', 'FAILED'
                self.assertFalse(True,e)
            finally:
                self.stopservers()

if __name__ == '__main__':
    unittest.main()
