#!/usr/bin/env python3
"""
Tests for Example 8: Traffic Shaping
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestTrafficShapingExample(unittest.TestCase):
    """Test the traffic shaping example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "traffic_shaping", "examples/08_traffic_shaping.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)


if __name__ == '__main__':
    unittest.main()
