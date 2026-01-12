#!/usr/bin/env python3
"""
Unit tests for marionette.multiplexer module.
"""

import sys
import unittest

sys.path.insert(0, '.')

import marionette.multiplexer
import marionette.record_layer


class TestMarionetteStream(unittest.TestCase):
    """Test MarionetteStream class."""

    def setUp(self):
        """Set up test fixtures."""
        self.incoming = marionette.multiplexer.BufferIncoming()
        self.outgoing = marionette.multiplexer.BufferOutgoing()
        self.stream_id = 12345

    def test_stream_creation(self):
        """Test creating a stream."""
        stream = marionette.multiplexer.MarionetteStream(
            self.incoming, self.outgoing, self.stream_id)
        
        self.assertEqual(stream.get_stream_id(), self.stream_id)
        self.assertEqual(stream.peek(), '')

    def test_stream_buffer_operations(self):
        """Test stream buffer operations."""
        stream = marionette.multiplexer.MarionetteStream(
            self.incoming, self.outgoing, self.stream_id)
        
        # Test peek on empty buffer
        self.assertEqual(stream.peek(), '')
        
        # Test pop on empty buffer
        buffer = stream.pop()
        self.assertEqual(buffer, '')

    def test_stream_terminate(self):
        """Test terminating a stream."""
        stream = marionette.multiplexer.MarionetteStream(
            self.incoming, self.outgoing, self.stream_id)
        
        # Should not raise exception
        stream.terminate()


class TestBufferOutgoing(unittest.TestCase):
    """Test BufferOutgoing class."""

    def setUp(self):
        """Set up test fixtures."""
        self.buffer = marionette.multiplexer.BufferOutgoing()

    def test_buffer_creation(self):
        """Test creating a buffer."""
        self.assertIsNotNone(self.buffer)

    def test_terminate_stream(self):
        """Test terminating a stream."""
        stream_id = 1
        
        # Should not raise exception
        self.buffer.terminate(stream_id)


class TestBufferIncoming(unittest.TestCase):
    """Test BufferIncoming class."""

    def setUp(self):
        """Set up test fixtures."""
        self.buffer = marionette.multiplexer.BufferIncoming()

    def test_buffer_creation(self):
        """Test creating a buffer."""
        self.assertIsNotNone(self.buffer)

    def test_add_callback(self):
        """Test adding callback."""
        callback_called = []
        
        def test_callback(cell):
            callback_called.append(cell)
        
        # Should not raise exception
        self.buffer.addCallback(test_callback)


if __name__ == '__main__':
    unittest.main()
