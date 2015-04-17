import os
import time
import httplib
import unittest
import threading

def execute(cmd):
    os.system(cmd)

def exec_download():
    conn = httplib.HTTPConnection("127.0.0.1", 18079, False, timeout=5)
    conn.request("GET", "/")
    response = conn.getresponse()
    actual_response = response.read()
    conn.close()

    expected_response = ''.join([str(x) for x in range(2**16)])

    #print [actual_response[:32], expected_response[:32]]
    #print actual_response
    assert actual_response == expected_response

    return actual_response

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

    def dodownload_serial(self):
        total_elapsed = 0
        for i in range(1,11):
            start = time.time()

            exec_download()

            elapsed = time.time() - start
            total_elapsed += elapsed

            #print ['serial-1', i, elapsed, total_elapsed/i]

    def dodownload_parallel(self):
        simultaneous = 10
        total_elapsed = 0
        for i in range(1,11):
            start = time.time()

            threads = []
            for j in range(simultaneous):
                t = threading.Thread(target=exec_download)
                threads.append(t)
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            elapsed = time.time() - start
            total_elapsed += elapsed

            #print ['parallel-'+str(simultaneous), i, elapsed, total_elapsed/i]

    def test_cli_curl(self):
        try:
            self.startservers()
            self.dodownload_serial()
            self.dodownload_parallel()
        finally:
            self.stopservers()

if __name__ == '__main__':
    unittest.main()
