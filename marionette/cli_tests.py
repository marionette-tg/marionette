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

    assert actual_response == expected_response

    return actual_response

class Tests(unittest.TestCase):

    def startservers(self, format):
        execute("./bin/httpserver 18081 %s &" % format)
        execute("./bin/marionette_server 127.0.0.1 18081 %s &" % format)
        time.sleep(1)
        execute("./bin/marionette_client 127.0.0.1 18079 %s &" % format)
        time.sleep(1)

    def stopservers(self):
        execute("pkill -9 -f marionette_client")
        execute("pkill -9 -f marionette_server")
        execute("pkill -9 -f httpserver")

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
        print ''
        for format in ['http_simple_blocking',
                       'http_simple_nonblocking',
                       'ssh_simple_nonblocking',
                       'smb_simple_nonblocking',
                       ]:
            try:
                self.startservers(format)
                self.dodownload_serial()
                #self.dodownload_parallel()
                print '\t', format, '...', 'SUCCESS'
            except:
                print '\t', format, '...', 'FAILED'
            finally:
                self.stopservers()

if __name__ == '__main__':
    unittest.main()
