#!/usr/bin/env python3
"""
Tests for Example 10: Custom Protocol
"""

import sys
import unittest
import tempfile
import os

sys.path.insert(0, '.')


class TestCustomProtocolExample(unittest.TestCase):
    """Test the custom protocol example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "custom_protocol", "examples/10_custom_protocol.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_create_format_file(self):
        """Test creating a format file."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "custom_protocol", "examples/10_custom_protocol.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            format_path = module.create_format_file(
                'test_protocol', 
                'connection(tcp, 1234):\n  start client NULL 1.0',
                tmpdir
            )
            self.assertTrue(os.path.exists(format_path))


if __name__ == '__main__':
    unittest.main()
