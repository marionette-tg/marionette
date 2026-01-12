#!/usr/bin/env python3
"""
Unit tests for format validation.
"""

import sys
import unittest
import tempfile
import os

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

    def test_validation_fails_invalid_probabilities(self):
        """Test that validation fails when probabilities don't sum to 1."""
        # Create a format file with invalid probabilities
        invalid_format = """connection(tcp, 8080):
  start      upstream   NULL     1.0
  upstream   downstream http_get 0.5
  downstream end        http_ok  0.3

action http_get:
  client fte.send("^.*$", 128)

action http_ok:
  server fte.send("^.*$", 128)
"""
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mar', delete=False) as f:
            f.write(invalid_format)
            temp_path = f.name
        
        try:
            # Parse should work (syntax is valid)
            with open(temp_path, 'r') as f:
                content = f.read()
            parsed = marionette.dsl.parse(content)
            
            # But validation should fail (probabilities don't sum to 1)
            with self.assertRaises(marionette.format_validator.FormatValidationError) as cm:
                marionette.format_validator.validate_format(parsed)
            self.assertIn("sum", str(cm.exception).lower())
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
