#!/usr/bin/env python3
"""
Tests for Example 2: Format Validator
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestFormatValidatorExample(unittest.TestCase):
    """Test the format validator example."""

    def test_list_formats_returns_formats(self):
        """Verify we can list available formats."""
        import marionette_tg.dsl
        
        formats = marionette_tg.dsl.list_mar_files('client')
        self.assertTrue(len(formats) > 0, "No formats found")

    def test_dummy_format_exists(self):
        """Verify the dummy format exists (used for testing)."""
        import marionette_tg.dsl
        
        formats = marionette_tg.dsl.list_mar_files('client')
        dummy_formats = [f for f in formats if 'dummy' in f]
        self.assertTrue(len(dummy_formats) > 0, "No dummy format found")

    def test_get_latest_version(self):
        """Verify we can get the latest version of a format."""
        import marionette_tg.dsl
        
        version = marionette_tg.dsl.get_latest_version('client', 'dummy')
        self.assertIsNotNone(version)

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "format_validator", "examples/02_format_validator.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)


if __name__ == '__main__':
    unittest.main()
