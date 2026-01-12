#!/usr/bin/env python3
"""
Tests for Example 7: Multi-Format Switching
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestMultiFormatExample(unittest.TestCase):
    """Test the multi-format switching example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "multi_format", "examples/07_multi_format_switching.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_format_switcher_class(self):
        """Verify FormatSwitcher class exists."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "multi_format", "examples/07_multi_format_switching.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        switcher = module.FormatSwitcher(['format1', 'format2'], 30)
        self.assertEqual(switcher.get_current_format(), 'format1')
        switcher.switch_format()
        self.assertEqual(switcher.get_current_format(), 'format2')


if __name__ == '__main__':
    unittest.main()
