#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for persistency layer for data from senec.py
"""

import os
import logging
import unittest

from .senec_db import SenecDB

log = logging.getLogger("SenecDB-Tests")

class TestSenecDBMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.db = SenecDB("./", "test.db")

    def tearDown(self) -> None:
        self.db.cursor.close()
        self.db.connection.close()
        os.remove("./test.db")

    def test_insert_value(self):
        self.db.insert_measurement(5.5)
        self.assertEqual(self.db.cursor.execute("SELECT * FROM senec LIMIT 1").fetchone()[1], 5.5, 'inserted value does not match')


if __name__ == '__main__':
    unittest.main()