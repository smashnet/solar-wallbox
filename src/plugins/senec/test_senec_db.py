#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for persistency layer for data from senec.py
"""

import os
import logging
import unittest
from datetime import datetime

from .senec_db import SenecDB

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("SenecDB-Tests")
db_file = "./test.db"

class TestSenecDBMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.db = SenecDB(db_file)

    def tearDown(self) -> None:
        self.db.cursor.close()
        self.db.connection.close()
        os.remove(db_file)

    def test_read_max_pv_production_between_timestamps(self) -> None:
        # Arrange
        m1 = Measurement()
        m2 = Measurement()
        m1.setLivePVProduction(300.0)
        m2.setLivePVProduction(266.1)
        insert_m1_at_ts = datetime.fromisoformat("2021-04-22 13:22:53")
        insert_m2_at_ts = datetime.fromisoformat("2021-04-22 13:47:41")

        # Act
        self.db.insert_measurement_with_custom_ts(m1.getData(), insert_m1_at_ts)
        self.db.insert_measurement_with_custom_ts(m2.getData(), insert_m2_at_ts)

        # Assert
        self.assertEqual(
            self.db.get_max_val_between_tss("live_pv_production", datetime.fromisoformat("2021-04-22 13:00:00"), datetime.fromisoformat("2021-04-22 14:00:00")),
            300.0,
            'Max val between tss not as expected')

class Measurement():

    def __init__(self) -> None:
        self.data = {"general": {"current_state": "CHARGE", "hours_of_operation": 0},
                     "live_data": {"house_power": 0.0, "pv_production": 0.0, "grid_power": 0.0, "battery_charge_power": 0.0, "battery_charge_current": 0.0, "battery_voltage": 0.0, "battery_percentage": 0.0},
                     "battery_information": {"design_capacity": 0.0, "max_charge_power": 0.0, "max_discharge_power": 0.0, "cycles": [0, 0, 0, 0], "charged_energy": [0, 0, 0, 0], "discharged_energy": [0, 0, 0, 0]},
                     "statistics": {"timestamp": 0, "battery_charged_energy": 0.0, "battery_discharged_energy": 0.0, "grid_export": 0.0, "grid_import": 0.0, "house_consumption": 0.0, "pv_production": 0.0}}

    def setStatGridExport(self, value):
        self.data['statistics']['grid_export'] = value

    def setStatPVProduction(self, value):
        self.data['statistics']['pv_production'] = value

    def setLivePVProduction(self, value):
        self.data['live_data']['pv_production'] = value

    def getData(self):
        return self.data

if __name__ == '__main__':
    unittest.main()