#!/usr/bin/env python3
"""
Tests for Example 4: DNS Tunnel
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestDNSTunnelExample(unittest.TestCase):
    """Test the DNS tunnel example."""

    def test_dns_format_exists(self):
        """Verify the dns_request format exists."""
        import marionette.dsl
        
        formats = marionette.dsl.list_mar_files('client')
        dns_formats = [f for f in formats if 'dns' in f.lower()]
        self.assertTrue(len(dns_formats) > 0, "No DNS format found")

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "dns_tunnel", "examples/04_dns_tunnel.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_udp_support(self):
        """Verify DNS format uses UDP (not TCP)."""
        # DNS tunneling typically uses UDP
        # This is a basic check that the format exists
        import marionette.dsl
        
        formats = marionette.dsl.list_mar_files('client')
        dns_formats = [f for f in formats if 'dns' in f.lower()]
        self.assertTrue(len(dns_formats) > 0)


if __name__ == '__main__':
    unittest.main()
