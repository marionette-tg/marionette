import os
import time
import socks
import socket
import httplib
import unittest

def execute(cmd):
    os.system(cmd)

def kpdyercom():
    return '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>302 Found</title>\n</head><body>\n<h1>Found</h1>\n<p>The document has moved <a href="https://kpdyer.com/">here</a>.</p>\n<hr>\n<address>Apache/2.4.7 (Ubuntu) Server at kpdyer.com Port 80</address>\n</body></html>\n'

class Tests(unittest.TestCase):

    def setproxy(self):
        self.socket_no_proxy_ = socket.socket
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, "127.0.0.1", 18079)
        socket.socket = socks.socksocket

    def unsetproxy(self):
        socket.socket = self.socket_no_proxy_

    def dodownload(self):
        try:
            conn = httplib.HTTPConnection("kpdyer.com")
            conn.request("GET", "/")
            print ['sw', 'conn.getresponse()']
            self.fail()
        except socks.ProxyConnectionError:
            pass

        execute("./bin/marionette_socks 18081 &")
        time.sleep(0.5)
        execute("./bin/marionette_server 127.0.0.1 18081 &")
        time.sleep(0.5)
        execute("./bin/marionette_client 127.0.0.1 18079 &")

        time.sleep(1)

        for i in range(1):
            try:
                start = time.time()
                conn = httplib.HTTPConnection("kpdyer.com")
                conn.request("GET", "/")
                response = conn.getresponse()
                contents = response.read()
                elapsed = time.time() - start
                print [elapsed]
                self.assertEqual(kpdyercom(), contents)
                conn.close()
            except Exception as e:
                self.fail(e)

    def killall(self):
        execute("pkill -9 -f marionette_client")
        execute("pkill -9 -f marionette_server")
        execute("pkill -9 -f marionette_socks")

    def test_cli_curl(self):
        try:
            self.setproxy()
            self.killall()
            self.dodownload()
        finally:
            self.killall()
            self.unsetproxy()

if __name__ == '__main__':
    unittest.main()
