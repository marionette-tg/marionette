#!/usr/bin/env python3
"""
Tests for Example 9: Format Comparison
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestFormatComparisonExample(unittest.TestCase):
    """Test the format comparison example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "format_comparison", "examples/09_format_comparison.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_get_format_info(self):
        """Verify get_format_info function works."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "format_comparison", "examples/09_format_comparison.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test with dummy format
        info = module.get_format_info('dummy')
        self.assertIn('name', info)
        self.assertEqual(info['name'], 'dummy')


if __name__ == '__main__':
    unittest.main()
