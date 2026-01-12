#!/usr/bin/env python3
"""
Unit tests for marionette.conf module.
"""

import sys
import unittest
import tempfile
import os

sys.path.insert(0, '.')

import marionette.conf


class TestConf(unittest.TestCase):
    """Test configuration module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_conf = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
        self.temp_conf.write("""[general]
debug = False
autoupdate = False
update_server = example.com
format = dummy

[client]
client_ip = 127.0.0.1
client_port = 8079

[server]
server_ip = 127.0.0.1
proxy_ip = 127.0.0.1
proxy_port = 8081
""")
        self.temp_conf.close()
        
        # Temporarily replace find_conf_file to use our temp file
        self.original_find = marionette.conf.find_conf_file
        marionette.conf.find_conf_file = lambda: self.temp_conf.name

    def tearDown(self):
        """Clean up test fixtures."""
        marionette.conf.find_conf_file = self.original_find
        if os.path.exists(self.temp_conf.name):
            os.unlink(self.temp_conf.name)
        # Reset conf_ dict
        if hasattr(marionette.conf, 'conf_'):
            delattr(marionette.conf, 'conf_')

    def test_find_conf_file(self):
        """Test finding configuration file."""
        # Reset to test original function
        marionette.conf.find_conf_file = self.original_find
        
        # Should find the conf file in marionette directory
        conf_path = marionette.conf.find_conf_file()
        self.assertIsNotNone(conf_path)
        self.assertTrue(os.path.exists(conf_path))

    def test_get_config_value(self):
        """Test getting configuration values."""
        # Parse config
        marionette.conf.parse_conf()
        
        # Test getting values
        debug = marionette.conf.get("general.debug")
        self.assertFalse(debug)
        
        client_ip = marionette.conf.get("client.client_ip")
        self.assertEqual(client_ip, "127.0.0.1")
        
        client_port = marionette.conf.get("client.client_port")
        self.assertEqual(client_port, 8079)

    def test_set_config_value(self):
        """Test setting configuration values."""
        # Parse config first
        marionette.conf.parse_conf()
        
        # Set a value
        marionette.conf.set("general.debug", True)
        
        # Get it back
        debug = marionette.conf.get("general.debug")
        self.assertTrue(debug)
        
        # Set another value
        marionette.conf.set("client.client_port", 9999)
        port = marionette.conf.get("client.client_port")
        self.assertEqual(port, 9999)

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        marionette.conf.parse_conf()
        
        # Should raise KeyError or handle gracefully
        with self.assertRaises((KeyError, AttributeError)):
            marionette.conf.get("nonexistent.key")


if __name__ == '__main__':
    unittest.main()
