import os
import time
import httplib
import unittest

def execute(cmd):
    os.system(cmd)

class Tests(unittest.TestCase):

    def startservers(self):
        execute("./bin/httpserver 18081 &")
        time.sleep(0.5)
        execute("./bin/marionette_server 127.0.0.1 18081 &")
        time.sleep(0.5)
        execute("./bin/marionette_client 127.0.0.1 18079 &")
        time.sleep(0.5)

    def stopservers(self):
        execute("pkill -9 -f marionette_client")
        execute("pkill -9 -f marionette_server")
        execute("pkill -9 -f httpserver")
        time.sleep(1)

    def dodownload(self):
        for i in range(10):
            start = time.time()
            conn = httplib.HTTPConnection("127.0.0.1", 18079, False, timeout=5)
            conn.request("GET", "/")
            response = conn.getresponse()
            actual_response = response.read()
            conn.close()
            elapsed = time.time() - start
            #print [i, elapsed]
            expected_response = ''.join([str(x) for x in range(2**16)])
            self.assertEqual(expected_response, actual_response)

    def test_cli_curl(self):
        try:
            self.startservers()
            self.dodownload()
        finally:
            self.stopservers()

if __name__ == '__main__':
    unittest.main()
