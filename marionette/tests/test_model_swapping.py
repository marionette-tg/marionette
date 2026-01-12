import sys
import unittest

from twisted.internet import reactor

sys.path.append('.')

import marionette

class Tests(unittest.TestCase):

    def test_model_swapping1(self):
        # do initial setup
        client = marionette.Client('http_simple_blocking',
                                      '20150701')

        expected_format = 'http_simple_blocking:20150701'
        actual_format = client.get_format()
        self.assertEqual(expected_format, actual_format)

        # simulate update
        # ... downloaded 20150702 ...
        # the update will call client.reload_driver
        client.reload_driver()

        # simulate the driver running to completion
        # this could also be done by actually having the client connect
        # to a server, but in its default state it has an initial, active model
        client.driver_.stop()

        # do one execution of the client, which will invoke the swap
        client.execute(reactor)

        # verify that the swap actually happened
        expected_format = 'http_simple_blocking:20150702'
        actual_format = client.get_format()
        self.assertEqual(expected_format, actual_format)

if __name__ == "__main__":
    unittest.main()
