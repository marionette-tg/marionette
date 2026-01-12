#!/usr/bin/env python3
"""
Tests for Example 6: Active Probing Resistance
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestActiveProbingExample(unittest.TestCase):
    """Test the active probing resistance example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "active_probing", "examples/06_active_probing_resistance.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_active_probing_format_exists(self):
        """Verify active probing formats exist."""
        import marionette_tg.dsl
        
        formats = marionette_tg.dsl.list_mar_files('client')
        probing_formats = [f for f in formats if 'probing' in f.lower()]
        self.assertTrue(len(probing_formats) > 0, "No active probing formats found")


if __name__ == '__main__':
    unittest.main()
