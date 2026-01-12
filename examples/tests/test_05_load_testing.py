#!/usr/bin/env python3
"""
Tests for Example 5: Load Testing
"""

import sys
import unittest

sys.path.insert(0, '.')


class TestLoadTestingExample(unittest.TestCase):
    """Test the load testing example."""

    def test_example_imports(self):
        """Verify the example script can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "load_testing", "examples/05_load_testing.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(module)

    def test_load_test_result_class(self):
        """Verify LoadTestResult class exists and works."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "load_testing", "examples/05_load_testing.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        result = module.LoadTestResult()
        result.add_result(True, 0.1, 1024)
        stats = result.get_stats()
        
        self.assertIn('total_requests', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('avg_latency', stats)


if __name__ == '__main__':
    unittest.main()
