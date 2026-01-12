#!/usr/bin/env python3
"""
Unit tests for marionette.exceptions module.
"""

import sys
import unittest

sys.path.insert(0, '.')

import marionette.exceptions


class TestExceptions(unittest.TestCase):
    """Test exception classes."""

    def test_marionette_exception(self):
        """Test MarionetteException can be raised and caught."""
        with self.assertRaises(marionette.exceptions.MarionetteException):
            raise marionette.exceptions.MarionetteException("Test error")

    def test_marionette_exception_message(self):
        """Test MarionetteException with message."""
        try:
            raise marionette.exceptions.MarionetteException("Custom error message")
        except marionette.exceptions.MarionetteException as e:
            self.assertEqual(str(e), "Custom error message")

    def test_marionette_exception_inheritance(self):
        """Test MarionetteException inherits from Exception."""
        self.assertTrue(issubclass(
            marionette.exceptions.MarionetteException, Exception))


if __name__ == '__main__':
    unittest.main()
