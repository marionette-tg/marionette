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
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, "127.0.0.1", 8079)
        socket.socket = socks.socksocket

    def unsetproxy(self):
        socket.socket = self.socket_no_proxy_

    def dodownload(self):
        try:
            conn = httplib.HTTPConnection("kpdyer.com")
            conn.request("GET", "/")
            self.fail()
        except socks.ProxyConnectionError:
            pass

        execute("./bin/marionette_socks 8081 &")
        execute("./bin/marionette_server 8080 127.0.0.1 8081 &")
        execute("./bin/marionette_client 8079 127.0.0.1 8080 &")

        time.sleep(1)

        try:
            conn = httplib.HTTPConnection("kpdyer.com")
            conn.request("GET", "/")
            response = conn.getresponse()
            self.assertEqual(kpdyercom(), response.read())
        except Exception as e:
            print e
            self.fail()

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
