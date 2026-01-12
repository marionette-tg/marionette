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

<<<<<<< HEAD
    def test_validate_existing_format(self):
        """Test validation of an existing format file."""
        # Use an actual format file that we know parses correctly
        with open('marionette/formats/20150701/dummy.mar', 'r') as f:
            content = f.read()
        
        parsed = marionette.dsl.parse(content)
=======
    def test_valid_format(self):
        """Test validation of a valid format."""
        format_str = """
connection(tcp, 8080):
  start client NULL 1.0
  client end http_ok 1.0

action http_ok:
  server fte.send("^.*$", 128)
"""
        parsed = marionette.dsl.parse(format_str)
        # Should not raise
        marionette.format_validator.validate_format(parsed)

    def test_missing_start_state(self):
        """Test validation fails when start state is missing."""
        format_str = """
connection(tcp, 8080):
  client end http_ok 1.0

action http_ok:
  server fte.send("^.*$", 128)
"""
        parsed = marionette.dsl.parse(format_str)
        with self.assertRaises(marionette.format_validator.FormatValidationError) as cm:
            marionette.format_validator.validate_format(parsed)
        self.assertIn("start", str(cm.exception))

    def test_probabilities_not_sum_to_one(self):
        """Test validation fails when probabilities don't sum to 1."""
        format_str = """
connection(tcp, 8080):
  start client NULL 0.5
  client end http_ok 0.3

action http_ok:
  server fte.send("^.*$", 128)
"""
        parsed = marionette.dsl.parse(format_str)
        with self.assertRaises(marionette.format_validator.FormatValidationError) as cm:
            marionette.format_validator.validate_format(parsed)
        self.assertIn("sum", str(cm.exception).lower())

    def test_no_path_to_end(self):
        """Test validation fails when there's no path to end state."""
        format_str = """
connection(tcp, 8080):
  start client NULL 1.0
  client client loop 1.0
  end end NULL 1.0

action loop:
  client fte.send("^.*$", 128)
"""
        parsed = marionette.dsl.parse(format_str)
        with self.assertRaises(marionette.format_validator.FormatValidationError) as cm:
            marionette.format_validator.validate_format(parsed)
        self.assertIn("path", str(cm.exception).lower())

    def test_error_transitions_excluded_from_probability_sum(self):
        """Test that error transitions don't count toward probability sum."""
        format_str = """
connection(tcp, 8080):
  start client NULL 1.0
  client end http_ok 1.0
  client end_err NULL error

action http_ok:
  server fte.send("^.*$", 128)
"""
        parsed = marionette.dsl.parse(format_str)
        # Should not raise - error transitions are excluded
        marionette.format_validator.validate_format(parsed)

    def test_probabilistic_format(self):
        """Test validation with probabilistic transitions."""
        format_str = """
connection(tcp, 8080):
  start client NULL 1.0
  client end http_ok 0.7
  client end http_error 0.3

action http_ok:
  server fte.send("^.*$", 128)

action http_error:
  server fte.send("^.*$", 64)
"""
        parsed = marionette.dsl.parse(format_str)
>>>>>>> 89dfd07 (Remove validation from load() - keep as standalone utility)
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

<<<<<<< HEAD
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

=======
>>>>>>> 89dfd07 (Remove validation from load() - keep as standalone utility)

if __name__ == '__main__':
    unittest.main()
