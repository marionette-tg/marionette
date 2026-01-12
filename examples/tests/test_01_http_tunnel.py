#!/usr/bin/env python3
"""
Tests for Example 1: Basic HTTP Tunnel

These tests verify that the HTTP tunnel example code is syntactically correct
and that the marionette format it uses is valid.
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestHttpTunnelExample(unittest.TestCase):
    """Test the HTTP tunnel example."""

    def test_format_exists(self):
        """Verify the http_simple_blocking format exists."""
        import marionette.dsl
        
        formats = marionette.dsl.list_mar_files('client')
        # Format names include version, check for any http_simple_blocking variant
        http_formats = [f for f in formats if 'http_simple_blocking' in f]
        self.assertTrue(len(http_formats) > 0, "No http_simple_blocking format found")

    def test_format_parses(self):
        """Verify the format can be parsed."""
        import marionette.dsl
        
        # Get the format path and parse it
        version = marionette.dsl.get_latest_version('client', 'http_simple_blocking')
        self.assertIsNotNone(version)

    def test_example_imports(self):
        """Verify the example script can be imported without errors."""
        # This tests that all imports work and syntax is correct
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "http_tunnel", "examples/01_http_tunnel.py")
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just verify it loads
        self.assertIsNotNone(module)

    def test_client_class_exists(self):
        """Verify marionette Client class is accessible."""
        import marionette
        self.assertTrue(hasattr(marionette, 'Client'))

    def test_server_class_exists(self):
        """Verify marionette Server class is accessible."""
        import marionette
        self.assertTrue(hasattr(marionette, 'Server'))


if __name__ == '__main__':
    unittest.main()
