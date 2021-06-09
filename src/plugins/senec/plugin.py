"""
Read and decode energy data from SENEC Home V3 Hybrid appliances.
"""
import os
import schedule
import time
import logging

import plugin_collection
from .senec import Senec
from .senec_db import SenecDB

log = logging.getLogger("Senec")

class SenecHomeV3Hybrid(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "SENEC.Home V3 hybrid (duo)"
        self.description = "Read and decode energy data from SENEC Home V3 Hybrid appliances."
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "source"
        self.has_runtime = True
        self.current_data = {}
        self.settings = { # Will be read from src/config/settings.json
            "plugin_path": "/senec",
            "device_ip": "IP_OF_YOUR_SENEC_DEVICE",
            "batteryCapacity": 10,
            "db_file": "path_to_db_file"
        }

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            self.settings['db_path'] = f"{settings['common']['db_base_path']}{self.settings['plugin_path']}"
            log.debug(f"Settings: {self.settings}")
            # Connect to SENEC appliance now that we have the IP address
            self.api = Senec(self.settings['device_ip'])

    def runtime(self, other_plugins):
        # This is run permanently in the background
        while True:
            # Get current data from appliance
            self.current_data.update(self.__getDataFromAppliance())
            
            # Store current data to DB
            db = SenecDB(f"{self.settings['db_path']}/{self.settings['db_file']}")
            db.insert_measurement(self.current_data)
            self.__insert_statistics_data(db)
            db.close()

            time.sleep(2)

    def endpoint(self, req, resp):
        viewmodel = self.__create_view_model(req)
        if (self.__get_output_format(req) == "json"):
            res = self.current_data
            resp.media = res
            return
        resp.html = self.webserver.render_template("senec/index.html", viewmodel)

    def getData(self):
        """
        getData can be used by other plugins.
        Plugins of type "source" should always use the structure shown in __getDataFromAppliance()
        """
        return self.current_data

    def __create_view_model(self, req):
        # Path: plugin_path + /
        return {
            "pluginPackage": self.pluginPackage,
            "name": type(self).__name__,
            "structure": self.__get_web_dict()
        }

    def __insert_statistics_data(self, db):
        self.current_data["live_data"]["house_power_min"] = db.get_todays_min("live_house_power")
        self.current_data["live_data"]["house_power_avg"] = db.get_todays_avg("live_house_power")
        self.current_data["live_data"]["house_power_max"] = db.get_todays_max("live_house_power")
        self.current_data["live_data"]["pv_production_min"] = db.get_todays_min("live_pv_production")
        self.current_data["live_data"]["pv_production_avg"] = db.get_todays_avg("live_pv_production")
        self.current_data["live_data"]["pv_production_max"] = db.get_todays_max("live_pv_production")
        self.current_data["live_data"]["grid_power_min"] = db.get_todays_min("live_grid_power")
        self.current_data["live_data"]["grid_power_avg"] = db.get_todays_avg("live_grid_power")
        self.current_data["live_data"]["grid_power_max"] = db.get_todays_max("live_grid_power")
        self.current_data["live_data"]["battery_charge_power_min"] = db.get_todays_min("live_battery_charge_power")
        self.current_data["live_data"]["battery_charge_power_avg"] = db.get_todays_avg("live_battery_charge_power")
        self.current_data["live_data"]["battery_charge_power_max"] = db.get_todays_max("live_battery_charge_power")
        self.current_data["statistics"]["house_consumption_today"] = db.get_todays("stats_house_consumption")
        self.current_data["statistics"]["pv_production_today"] = db.get_todays("stats_pv_production")
        self.current_data["statistics"]["battery_charged_energy_today"] = db.get_todays("stats_battery_charged_energy")
        self.current_data["statistics"]["battery_discharged_energy_today"] = db.get_todays("stats_battery_discharged_energy")
        self.current_data["statistics"]["grid_export_today"] = db.get_todays("stats_grid_export")
        self.current_data["statistics"]["grid_import_today"] = db.get_todays("stats_grid_import")


    def __getDataFromAppliance(self):
        appliance_values = self.api.get_values()
        if not "error" in appliance_values:
            # Transform senec data structure to our data structure
            return {
                "general": {
                    "current_state"         : appliance_values["STATISTIC"]["CURRENT_STATE"],                   # Current state of the system
                    "hours_of_operation"    : appliance_values["ENERGY"]["STAT_HOURS_OF_OPERATION"]             # Appliance hours of operation
                },
                "live_data": {
                    "house_power"           : appliance_values["ENERGY"]["GUI_HOUSE_POW"],                      # House power consumption (W)
                    "pv_production"         : appliance_values["ENERGY"]["GUI_INVERTER_POWER"],                 # PV production (W)
                    "grid_power"            : appliance_values["ENERGY"]["GUI_GRID_POW"],                       # Grid power: negative if exporting, positiv if importing (W)
                    "battery_charge_power"  : appliance_values["ENERGY"]["GUI_BAT_DATA_POWER"],                 # Battery charge power: negative if discharging, positiv if charging (W)
                    "battery_charge_current": appliance_values["ENERGY"]["GUI_BAT_DATA_CURRENT"],               # Battery charge current: negative if discharging, positiv if charging (A)
                    "battery_voltage"       : appliance_values["ENERGY"]["GUI_BAT_DATA_VOLTAGE"],               # Battery voltage (V)
                    "battery_percentage"    : appliance_values["ENERGY"]["GUI_BAT_DATA_FUEL_CHARGE"]            # Remaining battery (percent)
                },
                "battery_information": {
                    "design_capacity"       : appliance_values["FACTORY"]["DESIGN_CAPACITY"],                   # Battery design capacity (Wh)
                    "max_charge_power"      : appliance_values["FACTORY"]["MAX_CHARGE_POWER_DC"],               # Battery max charging power (W)
                    "max_discharge_power"   : appliance_values["FACTORY"]["MAX_DISCHARGE_POWER_DC"],            # Battery max discharging power (W)
                    "cycles"                : appliance_values["BMS"]["CYCLES"],                                # List: Cycles per battery
                    "charged_energy"        : appliance_values["BMS"]["CHARGED_ENERGY"],                        # List: Charged energy per battery
                    "discharged_energy"     : appliance_values["BMS"]["DISCHARGED_ENERGY"]                      # List: Discharged energy per battery
                },
                "statistics": {
                    "timestamp"                 : appliance_values["STATISTIC"]["MEASURE_TIME"],                # Unix timestamp for above values (ms)
                    "battery_charged_energy"    : appliance_values["STATISTIC"]["LIVE_BAT_CHARGE_MASTER"],      # Battery charge amount since installation (kWh)
                    "battery_discharged_energy" : appliance_values["STATISTIC"]["LIVE_BAT_DISCHARGE_MASTER"],   # Battery discharge amount since installation (kWh)
                    "grid_export"               : appliance_values["STATISTIC"]["LIVE_GRID_EXPORT"],            # Grid export amount since installation (kWh)
                    "grid_import"               : appliance_values["STATISTIC"]["LIVE_GRID_IMPORT"],            # Grid import amount since installation (kWh)
                    "house_consumption"         : appliance_values["STATISTIC"]["LIVE_HOUSE_CONS"],             # House consumption since installation (kWh)
                    "pv_production"             : appliance_values["STATISTIC"]["LIVE_PV_GEN"]                  # PV generated power since installation (kWh)
                }
            }

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __get_web_dict(self):
        '''
        {
            "title": "Test Chart",
            "type": "chartcard",
            "current_val_id": "testChartCard",
            "chart_id": "testChart",
            "icons": [
                {"name": "house", "size": 48, "fill": "currentColor"}
            ]
        },
        '''
        return {
            "groups": [
                {
                    "title": "Consumption and Production",
                    "blocks": [
                        {
                            "id": "housePower",
                            "title": "Consumption",
                            "type": "square",
                            "icons": [
                                {"name": "house", "size": 48, "fill": "currentColor"}
                            ],
                            "stats": [
                                {
                                "name": "Min",
                                "id": "housePower_min"
                                },
                                {
                                "name": "Avg",
                                "id": "housePower_avg"
                                },
                                {
                                "name": "Max",
                                "id": "housePower_max"
                                }
                            ]
                        },
                        {
                            "id": "pvProduction",
                            "title": "Production",
                            "type": "square",
                            "icons": [
                                {"name": "sun", "size": 48, "fill": "currentColor"}
                            ],
                            "stats": [
                                {
                                "name": "Min",
                                "id": "pvProduction_min"
                                },
                                {
                                "name": "Avg",
                                "id": "pvProduction_avg"
                                },
                                {
                                "name": "Max",
                                "id": "pvProduction_max"
                                }
                            ]
                        },
                        {
                            "id": "gridPower",
                            "title": "Grid Power",
                            "type": "square",
                            "icons": [
                                {"name": "lightning", "size": 48, "fill": "currentColor"}
                            ],
                            "stats": [
                                {
                                "name": "Min",
                                "id": "gridPower_min"
                                },
                                {
                                "name": "Avg",
                                "id": "gridPower_avg"
                                },
                                {
                                "name": "Max",
                                "id": "gridPower_max"
                                }
                            ]
                        },
                        {
                            "id": "batteryPower",
                            "title": "Battery Power",
                            "type": "square",
                            "icons": [
                                {"name": "battery-full", "size": 48, "fill": "currentColor"}
                            ],
                            "stats": [
                                {
                                "name": "Min",
                                "id": "batteryPower_min"
                                },
                                {
                                "name": "Avg",
                                "id": "batteryPower_avg"
                                },
                                {
                                "name": "Max",
                                "id": "batteryPower_max"
                                }
                            ]
                        }
                    ]
                },
                {
                    "title": "Battery",
                    "blocks": [
                        {
                            "id": "batteryVoltage",
                            "title": "Voltage",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "batteryCurrent",
                            "title": "Current",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "batteryPercentage",
                            "title": "Charge Level",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "batteryRemainingTime",
                            "title": "Remaining Time",
                            "type": "square",
                            "icons": []
                        }
                    ]
                },
                {
                    "title": "Statistics",
                    "prelude": "Accumulated values since system installation:",
                    "blocks": [
                        {
                            "id": "houseConsumptionStats",
                            "title": "Consumption",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "houseConsumption_today"
                                }
                            ]
                        },
                        {
                            "id": "pvProductionStats",
                            "title": "Production",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "pvProduction_today"
                                }
                            ]
                        },
                        {
                            "id": "batteryChargedStats",
                            "title": "Bat. Charged",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "batteryCharged_today"
                                }
                            ]
                        },
                        {
                            "id": "batteryDischaredStats",
                            "title": "Bat. Discharged",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "batteryDischared_today"
                                }
                            ]
                        },
                        {
                            "id": "gridExportStats",
                            "title": "Grid Export",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "gridExport_today"
                                }
                            ]
                        },
                        {
                            "id": "gridImportStats",
                            "title": "Grid Import",
                            "type": "square",
                            "icons": [],
                            "stats": [
                                {
                                "name": "Today",
                                "id": "gridImport_today"
                                }
                            ]
                        },
                    ]
                },
                {
                    "title": "General",
                    "blocks": [
                        {
                            "type": "infocard",
                            "title": "",
                            "icons": [
                                {"name": "file-post", "size": 48, "fill": "currentColor"}
                            ],
                            "contents": [
                                {"name": "Current State", "id": "currentState"},
                                {"name": "Hours of Operation", "id": "opHours"},
                                {"name": "Battery Cycles", "id": "batCycles"},
                                {"name": "Battery Design Capacity", "id": "batDesignCapacity"},
                                {"name": "Battery Max Charge Power", "id": "batMaxChargePower"},
                                {"name": "Battery Max Discharge Power", "id": "batMaxDischargePower"}
                            ]
                        }
                    ]
                }
            ]
        }