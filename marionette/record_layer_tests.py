#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest
import random

sys.path.append('.')

import marionette.record_layer
import marionette.multiplexer


class Tests(unittest.TestCase):

    def test_serializeUnserialize_onBoundaries1(self):
        cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
        cell_expected.set_payload('XXX')
        cell_str = marionette.record_layer.serialize(cell_expected)
        cell_actual = marionette.record_layer.unserialize(cell_str)
        self.assertEqual(cell_actual, cell_expected)

    def test_serializeUnserialize_onBoundaries2(self):
        buffer = marionette.multiplexer.BufferIncoming()

        n = 100

        for i in range(n):
            cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
            cell_expected.set_payload('XXX' + str(i))
            cell_str = marionette.record_layer.serialize(cell_expected)
            buffer.push(cell_str)

        for i in range(n):
            cell_actual = buffer.pop()

            cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
            cell_expected.set_payload('XXX' + str(i))

            self.assertEqual(cell_actual, cell_expected)

    def test_serializeUnserialize_offBoundaries1(self):
        buffer = marionette.multiplexer.BufferIncoming()
        buffer.addCallback(None)

        n = 100

        for i in range(n):
            cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
            cell_expected.set_payload('XXX' + str(i))
            cell_str = marionette.record_layer.serialize(cell_expected)

            for c in cell_str:
                buffer.push(c)

        for i in range(n):
            cell_actual = buffer.pop()

            cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
            cell_expected.set_payload('XXX' + str(i))

            self.assertEqual(cell_actual, cell_expected)

    def test_pushPop_n1(self):
        cell_expected = marionette.record_layer.Cell(1, 1, 1, 0)
        cell_str = marionette.record_layer.serialize(cell_expected)

        buffer = marionette.multiplexer.BufferIncoming()
        buffer.push(cell_str)

        n = 1024
        cell_actual = buffer.pop()
        cell_str = marionette.record_layer.serialize(cell_actual, n)
        self.assertEqual(len(cell_str), n // 8)

    def test_pushPop_n2(self):
        buffer = marionette.multiplexer.BufferIncoming()

        cell_actual = buffer.pop()
        self.assertEqual(cell_actual, None)

    def test_pushPop_stream_id(self):
        for i in range(100):
            stream_id = random.randint(0, 2 ** 32)
            cell_expected = marionette.record_layer.Cell(1, 1,
                                                         stream_id, 0)
            cell_str = marionette.record_layer.serialize(cell_expected)

            buffer = marionette.multiplexer.BufferIncoming()
            buffer.push(cell_str)

            cell_actual = buffer.pop()
            self.assertEqual(cell_actual.get_stream_id(), stream_id)


if __name__ == '__main__':
    unittest.main()
