#!/usr/bin/env python
# coding: utf-8

import os
import sys
import time
import http.client
import unittest
import threading

sys.path.append('.')

import marionette.conf


def execute(cmd):
    os.system(cmd)


def exec_download():
    client_listen_ip = marionette.conf.get("client.client_ip")
    conn = http.client.HTTPConnection(
        client_listen_ip, 18079, timeout=30)
    conn.request("GET", "/")
    response = conn.getresponse()
    actual_response = response.read().decode('utf-8')
    conn.close()

    expected_response = ''
    for x in range(2**18):
        expected_response += '_' + str(x)

    assert actual_response == expected_response

    return actual_response


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """
    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(testcase_klass, param=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, param=param))
        return suite


class CliTest(ParametrizedTestCase):

    def startservers(self, format):
        client_listen_ip = marionette.conf.get("client.client_ip")
        server_proxy_ip = marionette.conf.get("server.proxy_ip")

        execute("./examples/httpserver --local_port 18081 &")
        execute("./bin/marionette_server --proxy_ip %s --proxy_port 18081 --format %s &" %
                (server_proxy_ip, format))
        time.sleep(5)
        execute("./bin/marionette_client --client_ip %s --client_port 18079 --format %s &" %
                (client_listen_ip, format))
        time.sleep(5)

    def stopservers(self):
        execute("pkill -9 -f marionette_client")
        execute("pkill -9 -f marionette_server")
        execute("pkill -9 -f httpserver")

    def dodownload_serial(self):
        exec_download()

    def dodownload_parallel(self):
        simultaneous = 2
        threads = []
        for j in range(simultaneous):
            t = threading.Thread(target=exec_download)
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def test_cli_curl(self):
        if self.param:
            try:
                format = self.param
                self.startservers(format)
                self.dodownload_serial()
                self.dodownload_parallel()
            except Exception as e:
                self.assertFalse(True, e)
            finally:
                sys.stdout.write(format+' ')
                sys.stdout.flush()
                self.stopservers()

suite = unittest.TestSuite()
for param in [
        'dummy',
        'http_timings',
        'ftp_simple_blocking',
        'http_simple_blocking',
        'http_simple_blocking:20150701', # tests in-band nego.
        'http_simple_blocking:20150702', # tests in-band nego.
        'http_squid_blocking',
        'http_simple_nonblocking',
        'http_probabilistic_blocking',
        'http_simple_blocking_with_msg_lens',
        'ssh_simple_nonblocking',
        'smb_simple_nonblocking',
        'http_active_probing',
        'http_active_probing2',
        'active_probing/http_apache_247',
        'active_probing/ssh_openssh_661',
        'active_probing/ftp_pureftpd_10']:
        suite.addTest(ParametrizedTestCase.parametrize(CliTest, param=param))

if __name__ == '__main__':
    testresult = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not testresult.wasSuccessful())
