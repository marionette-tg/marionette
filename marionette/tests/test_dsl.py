import sys
import unittest

sys.path.append('.')

import marionette.dsl


class Tests(unittest.TestCase):

    def test1(self):
        mar_format = """connection(tcp, 80):
          start      downstream NULL     1.0
          downstream upstream   http_get 1.0
          upstream   end        http_ok  1.0

        action http_get:
          client fte.send("^regex\\r\\n\\r\\n$", 128)

        action http_ok:
          server fte.send("^regex\\r\\n\\r\\n\\C*$", 128)"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), "http_get")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "upstream")
        self.assertEqual(parsed_format.get_transitions()[2].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(), "http_ok")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(), [
                "^regex\r\n\r\n$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "http_ok")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(), [
                "^regex\r\n\r\n\\C*$", 128])

    def test2(self):
        mar_format = """connection(tcp, 80):
          start      downstream NULL     1.0
          downstream upstream   http_get 1.0
          upstream   end        http_ok  1.0

        action http_get:
          client fte.send("^regex\\r\\n\\r\\n$", 128)

        action http_ok:
          server fte.send("^regex\\r\\n\\r\\n\\C*$", 128)

        action http_put:
          client fte.send("^regex\\r\\n\\r\\n$", 128)"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), "http_get")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "upstream")
        self.assertEqual(parsed_format.get_transitions()[2].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(), "http_ok")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(), [
                "^regex\r\n\r\n$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "http_ok")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(), [
                "^regex\r\n\r\n\\C*$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_name(), "http_put")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_args(), [
                "^regex\r\n\r\n$", 128])

    def test3(self):
        mar_format = """connection(tcp, 80):
          start      downstream NULL     1.0
          downstream upstream   http_get 1.0
          upstream   end        http_ok  1.0

        action http_get:
          client fte.send("^regex\\r\\n\\r\\n$", 128)

        action http_ok:
          server fte.send("^regex\\r\\n\\r\\n\\C*$", 128)

        action http_put:
          client fte.send("^regex\\r\\n\\r\\n$", 128)

        action http_notok:
          server fte.send("^regex\\r\\n\\r\\n\\C*$", 128)"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), "http_get")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "upstream")
        self.assertEqual(parsed_format.get_transitions()[2].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(), "http_ok")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(), [
                "^regex\r\n\r\n$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "http_ok")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(), [
                "^regex\r\n\r\n\\C*$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_name(), "http_put")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_args(), [
                "^regex\r\n\r\n$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[3].get_name(), "http_notok")
        self.assertEqual(
            parsed_format.get_action_blocks()[3].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[3].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[3].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[3].get_args(), [
                "^regex\r\n\r\n\\C*$", 128])

    def test4(self):
        mar_format = """connection(tcp, 8082):
  start      handshake  NULL               1.0
  handshake  upstream   upstream_handshake 1.0
  upstream   downstream upstream_async     1.0
  downstream upstream   downstream_async   1.0

action upstream_handshake:
  client fte.send("^.*$", 128)

action upstream_async:
  client fte.send_async("^.*$", 128)

action downstream_async:
  server fte.send_async("^.*$", 128)
"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 8082)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "handshake")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "handshake")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(),
            "upstream_handshake")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_dst(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(),
            "upstream_async")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[3].get_src(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[3].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[3].get_action_block(),
            "downstream_async")
        self.assertEqual(
            parsed_format.get_transitions()[3].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(),
            "upstream_handshake")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(), ["^.*$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "upstream_async")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "send_async")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(), ["^.*$", 128])

        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_name(),
            "downstream_async")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_method(), "send_async")
        self.assertEqual(
            parsed_format.get_action_blocks()[2].get_args(), ["^.*$", 128])

    def test5(self):
        mar_format = """connection(tcp, 80):
          start      downstream NULL     1.0
          downstream upstream   http_get 1.0
          upstream   end        http_ok  1.0

        action http_get:
          client fte.send("^regex\\r\\n\\r\\n$")

        action http_ok:
          server fte.send("^regex\\r\\n\\r\\n\\C*$")"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "downstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_dst(), "upstream")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), "http_get")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "upstream")
        self.assertEqual(parsed_format.get_transitions()[2].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(), "http_ok")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(1.0))

    def test6(self):
        mar_format = """connection(tcp, 80):
          start do_nothing NULL 1.0
          do_nothing end NULL 1.0

        action http_get:
          client fte.send("^regex1\\r\\n\\r\\n$")
          server fte.recv("^regex2\\r\\n\\r\\n$")"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "do_nothing")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "do_nothing")
        self.assertEqual(parsed_format.get_transitions()[1].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(),
            ["^regex1\r\n\r\n$"])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "recv")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(),
            ["^regex2\r\n\r\n$"])


    def test7(self):
        mar_format = """connection(tcp, 80):
          start do_nothing NULL 1.0
          do_nothing end NULL 1.0
          start do_err NULL error
          do_err end NULL error

        action http_get:
          client fte.send("^regex1\\r\\n\\r\\n$")"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "tcp")
        self.assertEqual(parsed_format.get_port(), 80)

        self.assertEqual(
            parsed_format.get_transitions()[0].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_dst(), "do_nothing")
        self.assertEqual(
            parsed_format.get_transitions()[0].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[0].get_probability(), float(1.0))
        self.assertEqual(
            parsed_format.get_transitions()[0].is_error_transition(), False)

        self.assertEqual(
            parsed_format.get_transitions()[1].get_src(), "do_nothing")
        self.assertEqual(parsed_format.get_transitions()[1].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[1].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[1].get_probability(), float(1.0))
        self.assertEqual(
            parsed_format.get_transitions()[1].is_error_transition(), False)

        self.assertEqual(
            parsed_format.get_transitions()[2].get_src(), "start")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_dst(), "do_err")
        self.assertEqual(
            parsed_format.get_transitions()[2].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[2].get_probability(), float(0))
        self.assertEqual(
            parsed_format.get_transitions()[2].is_error_transition(), True)

        self.assertEqual(
            parsed_format.get_transitions()[3].get_src(), "do_err")
        self.assertEqual(
            parsed_format.get_transitions()[3].get_dst(), "end")
        self.assertEqual(
            parsed_format.get_transitions()[3].get_action_block(), None)
        self.assertEqual(
            parsed_format.get_transitions()[3].get_probability(), float(0))
        self.assertEqual(
            parsed_format.get_transitions()[3].is_error_transition(), True)


    def test8(self):
        mar_format = """connection(tcp, 80):
          start do_nothing NULL 1.0
          do_nothing end NULL 1.0

        action http_get:
          client fte.send("^regex1\\r\\n\\r\\n$")
          server fte.recv("^regex2\\r\\n\\r\\n$") if regex_match_incoming("^regex2.*")"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_method(), "send")
        self.assertEqual(
            parsed_format.get_action_blocks()[0].get_args(),
            ["^regex1\r\n\r\n$"])

        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_name(), "http_get")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_party(), "server")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_module(), "fte")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_method(), "recv")
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_args(),
            ["^regex2\r\n\r\n$"])
        self.assertEqual(
            parsed_format.get_action_blocks()[1].get_regex_match_incoming(),"^regex2.*")

    def test9(self):
        mar_format = """connection(udp, 80):
          start do_nothing NULL 1.0
          do_nothing end NULL 1.0

        action http_get:
          client fte.send("^regex1\\r\\n\\r\\n$")"""

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_transport(), "udp")

    def test_hex_input_strings(self):
        mar_files = marionette.dsl.find_mar_files('client',
                                                     'test_hex_input_strings',
                                                     '20150701')
        with open(mar_files[0]) as f:
            mar_format = f.read()

        parsed_format = marionette.dsl.parse(mar_format)

        self.assertEqual(parsed_format.get_action_blocks()[0].get_name(), "null_puts")
        self.assertEqual(parsed_format.get_action_blocks()[0].get_party(), "client")
        self.assertEqual(parsed_format.get_action_blocks()[0].get_module(), "io")
        self.assertEqual(parsed_format.get_action_blocks()[0].get_method(), "puts")
        self.assertEqual(parsed_format.get_action_blocks()[0].get_args()[0], "\x41\x42\\backslash")


if __name__ == "__main__":
    unittest.main()
