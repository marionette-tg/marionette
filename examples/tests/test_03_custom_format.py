#!/usr/bin/env python3
"""
Tests for Example 3: Custom Format
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestCustomFormatExample(unittest.TestCase):
    """Test the custom format example."""

    def test_dsl_module_exists(self):
        """Verify DSL module is accessible."""
        import marionette_tg.dsl
        self.assertTrue(hasattr(marionette_tg.dsl, 'parse'))

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "custom_format", "examples/03_custom_format.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_format_constants_defined(self):
        """Verify format constants are defined in example."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "custom_format", "examples/03_custom_format.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.assertTrue(hasattr(module, 'EXAMPLE_FORMAT'))
        self.assertTrue(hasattr(module, 'PROBABILISTIC_FORMAT'))
        self.assertTrue(hasattr(module, 'ERROR_HANDLING_FORMAT'))


if __name__ == '__main__':
    unittest.main()
