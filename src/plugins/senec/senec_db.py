#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Persistency layer for data from senec.py
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta, timezone, date
import pytz

__author__ = "Nicolas Inden"
__copyright__ = "Copyright 2021, Nicolas Inden"
__credits__ = ["Nicolas Inden"]
__license__ = "Apache-2.0 License"
__version__ = "1.1.0"
__maintainer__ = "Nicolas Inden"
__email__ = "nico@smashnet.de"
__status__ = "Alpha"

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',level=logging.INFO)
log = logging.getLogger("SenecDB")
log.setLevel(logging.INFO)

class SenecDB():

    def __init__(self, db_file):
        self.db_path = os.path.dirname(db_file)
        self.db_filename = os.path.basename(db_file)
        self.db_full_path = db_file
        self.db_version = "0.0.1"
        self.timezone = pytz.timezone("Europe/Berlin")
        
        # Ensure directories exist
        try:
            os.makedirs(self.db_path)
        except FileExistsError:
            log.debug("DB path already exists.")

        # Establish connection
        self.connection = sqlite3.connect(self.db_full_path)
        self.cursor = self.connection.cursor()

        # Check if DB exists and is correct version
        try:
            version = self.cursor.execute("SELECT version FROM db_info").fetchone()[0]
            if version == self.db_version:
                log.debug(f"DB found and has correct version {version}. No migration needed :)")
            else:
                log.debug(f"Found DB, has version {version}. Target version is {self.db_version} ... migrating...")
                self.__migrate(version)
        except sqlite3.OperationalError:
            # db_info does not exist -> wrong or empty db_file
            log.debug("No not a valid DB file. Creating...")
            self.__init_tables_v0_0_1()

    def __init_tables_v0_0_1(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS db_info (version TEXT)")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS senec (
                                                    ts TIMESTAMP, 
                                                    stats_current_state TEXT, 
                                                    stats_battery_charged_energy FLOAT, 
                                                    stats_battery_discharged_energy FLOAT, 
                                                    stats_grid_export FLOAT, 
                                                    stats_grid_import FLOAT, 
                                                    stats_house_consumption FLOAT, 
                                                    stats_pv_production FLOAT, 
                                                    live_house_power FLOAT, 
                                                    live_pv_production FLOAT, 
                                                    live_grid_power FLOAT, 
                                                    live_battery_charge_power FLOAT, 
                                                    live_battery_charge_current FLOAT, 
                                                    live_battery_voltage FLOAT, 
                                                    live_battery_percentage FLOAT)""")
        self.cursor.execute(f"INSERT INTO db_info VALUES ('{self.db_version}')")
        self.connection.commit()

    def __migrate(self, from_version):
        # TODO
        log.error(f"Migration from DB version {from_version} to DB version {self.db_version} not yet implemented.")

    def close(self):
        self.cursor.close()
        self.connection.close()

    def insert_measurement(self, json):
        self.cursor.execute("INSERT INTO senec VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                        (json['general']['current_state'], 
                                                        json['statistics']['battery_charged_energy'], 
                                                        json['statistics']['battery_discharged_energy'], 
                                                        json['statistics']['grid_export'], 
                                                        json['statistics']['grid_import'], 
                                                        json['statistics']['house_consumption'], 
                                                        json['statistics']['pv_production'], 
                                                        json['live_data']['house_power'], 
                                                        json['live_data']['pv_production'], 
                                                        json['live_data']['grid_power'], 
                                                        json['live_data']['battery_charge_power'], 
                                                        json['live_data']['battery_charge_current'], 
                                                        json['live_data']['battery_voltage'], 
                                                        json['live_data']['battery_percentage']))
        self.connection.commit()

    def insert_measurement_with_custom_ts(self, json, datetime_ts):
        self.cursor.execute("INSERT INTO senec VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                        (datetime_ts,
                                                        json['general']['current_state'], 
                                                        json['statistics']['battery_charged_energy'], 
                                                        json['statistics']['battery_discharged_energy'], 
                                                        json['statistics']['grid_export'], 
                                                        json['statistics']['grid_import'], 
                                                        json['statistics']['house_consumption'], 
                                                        json['statistics']['pv_production'], 
                                                        json['live_data']['house_power'], 
                                                        json['live_data']['pv_production'], 
                                                        json['live_data']['grid_power'], 
                                                        json['live_data']['battery_charge_power'], 
                                                        json['live_data']['battery_charge_current'], 
                                                        json['live_data']['battery_voltage'], 
                                                        json['live_data']['battery_percentage']))
        self.connection.commit()

    def get_max_val_between_tss(self, column, ts1, ts2):
        log.debug(f"SELECT MAX({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'")
        return self.cursor.execute(f"SELECT MAX({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'").fetchone()[0]

    def get_min_val_between_tss(self, column, ts1, ts2):
        log.debug(f"SELECT MIN({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'")
        return self.cursor.execute(f"SELECT MIN({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'").fetchone()[0]

    def get_avg_val_between_tss(self, column, ts1, ts2):
        log.debug(f"SELECT AVERAGE({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'")
        return self.cursor.execute(f"SELECT AVERAGE({column}) FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}'").fetchone()[0]

    def get_diff_val_between_tss(self, column, ts1, ts2):
        log.debug(f"{column}, {ts1}, {ts2}")
        val1 = self.cursor.execute(f"SELECT {column} FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}' ORDER BY ts ASC LIMIT 1").fetchone()[0]
        val2 = self.cursor.execute(f"SELECT {column} FROM senec WHERE ts BETWEEN '{ts1.isoformat(sep=' ')}' AND '{ts2.isoformat(sep=' ')}' ORDER BY ts DESC LIMIT 1").fetchone()[0]
        return val2-val1

    def get_todays(self, metric):
        today_zero = datetime.now(tz=self.timezone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz=timezone.utc)
        today_now = datetime.utcnow()
        return self.get_diff_val_between_tss(metric, today_zero, today_now)

    def get_todays_max(self, metric):
        today_zero = datetime.now(tz=self.timezone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz=timezone.utc)
        today_now = datetime.utcnow()
        return self.get_max_val_between_tss(metric, today_zero, today_now)

    def get_todays_min(self, metric):
        today_zero = datetime.now(tz=self.timezone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz=timezone.utc)
        today_now = datetime.utcnow()
        return self.get_min_val_between_tss(metric, today_zero, today_now)

    def get_todays_avg(self, metric):
        today_zero = datetime.now(tz=self.timezone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(tz=timezone.utc)
        today_now = datetime.utcnow()
        return self.get_avg_val_between_tss(metric, today_zero, today_now)
