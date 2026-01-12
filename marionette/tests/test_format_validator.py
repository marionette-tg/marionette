#!/usr/bin/env python3
"""
Unit tests for format validation.
"""

import sys
import unittest

sys.path.insert(0, '.')

import marionette.dsl
import marionette.format_validator


class TestFormatValidator(unittest.TestCase):

    def test_validate_existing_format(self):
        """Test validation of an existing format file."""
        # Use an actual format file that we know parses correctly
        with open('marionette/formats/20150701/dummy.mar', 'r') as f:
            content = f.read()
        
        parsed = marionette.dsl.parse(content)
        # Should not raise
        marionette.format_validator.validate_format(parsed)

    def test_load_validates_format(self):
        """Test that validation can be applied to loaded formats."""
        # Load a format and validate it manually
        result = marionette.dsl.load('client', 'dummy', 'marionette/formats/20150701/dummy.mar')
        self.assertIsNotNone(result)
        
        # Validate by parsing and validating the format file directly
        with open('marionette/formats/20150701/dummy.mar', 'r') as f:
            content = f.read()
        parsed = marionette.dsl.parse(content)
        # Should not raise
        marionette.format_validator.validate_format(parsed)


if __name__ == '__main__':
    unittest.main()
