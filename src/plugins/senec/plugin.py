"""
Read and decode energy data from SENEC Home V3 Hybrid appliances.
"""
import os
import logging

import plugin_collection
from .senec import Senec

log = logging.getLogger("Senec")

class SenecHomeV3Hybrid(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "SENEC.Home V3 hybrid (duo)"
        self.description = "Read and decode energy data from SENEC Home V3 Hybrid appliances."
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "source"
        self.has_runtime = False
        self.settings = { # Will be read from src/config/settings.json
            "plugin_path": "/senec",
            "device_ip": "IP_OF_YOUR_SENEC_DEVICE"
        }

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")
            # Connect to SENEC appliance now that we have the IP address
            self.api = Senec(self.settings['device_ip'])

    def endpoint(self, req, resp):
        template_vars = {
            "pluginPackage": self.pluginPackage
        }
        template_vars['name'] = type(self).__name__
        if (self.__get_output_format(req) == "json"):
            res = self.getData()
            resp.media = res
            return
        res_web = self.__get_web_dict()
        self.__send_response(res_web, resp, template_vars)

    def getData(self):
        """
        getData can be used by other plugins.
        Plugins of type "source" should always use this structure:
        {
            "general": {
                "current_state"         : "charging",           # Current state of the system
                "hours_of_operation"    : 123                   # Appliance hours of operation
            },
            "live_data": {
                "house_power"           : 0.0,                  # House power consumption (W)
                "pv_production"         : 0.0,                  # PV production (W)
                "grid_power"            : 0.0,                  # Grid power: negative if exporting, positiv if importing (W)
                "battery_charge_power"  : 0.0,                  # Battery charge power: negative if discharging, positiv if charging (W)
                "battery_charge_current": 0.0,                  # Battery charge current: negative if discharging, positiv if charging (A)
                "battery_voltage"       : 0.0,                  # Battery voltage (V)
                "battery_percentage"    : 0.0                   # Remaining battery (percent)
            },
            "battery_information": {
                "design_capacity"       : 10000,                # Battery design capacity (Wh)
                "max_charge_power"      : 2500,                 # Battery max charging power (W)
                "max_discharge_power"   : 3750,                 # Battery max discharging power (W)
                "cycles"                : [bat1, bat2, ...]     # List: Cycles per battery
            },
            "statistics": {
                "timestamp"                 : 1606397884,
                "battery_charged_energy"    : 0.0,
                "battery_discharged_energy" : 0.0,
                "grid_export"               : 0.0,
                "grid_import"               : 0.0,
                "house_consumption"         : 0.0,
                "pv_production"             : 0.0
            }
        }
        """
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


    def __send_response(self, res_web, resp, template_vars):
        template_vars['res'] = res_web
        resp.html = self.webserver.render_template("senec/index.html", template_vars)

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __get_web_dict(self):
        return {
            "groups": [
                {
                    "title": "Consumption and Production",
                    "cards": [
                        {
                            "id": "housePower",
                            "title": "Consumption",
                            "icons": [
                                {"name": "house", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "inverterPower",
                            "title": "Production",
                            "icons": [
                                {"name": "sun", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Grid",
                    "cards": [
                        {
                            "id": "gridPull",
                            "title": "Demand",
                            "icons": [
                                {"name": "lightning", "size": 48, "fill": "currentColor"},
                                {"name": "arrow-right", "size": 28, "fill": "currentColor"}
                            ]
                        },
                        {
                        "id": "gridPush",
                        "title": "Supply",
                        "icons": [
                            {
                                "name": "arrow-right",
                                "size": 28,
                                "fill": "currentColor"
                            },
                            {
                                "name": "lightning",
                                "size": 48,
                                "fill": "currentColor"
                            }
                        ]
                        }
                    ]
                },
                {
                    "title": "Battery",
                    "cards": [
                        {
                        "id": "batteryCharge",
                        "icons": [
                            {
                                "name": "arrow-right",
                                "size": 28,
                                "fill": "currentColor"
                            },
                            {
                                "name": "battery-charging",
                                "size": 48,
                                "fill": "currentColor"
                            }
                        ],
                        "title": "Charging"
                        },
                        {
                        "id": "batteryDischarge",
                        "icons": [
                            {
                                "name": "battery-half",
                                "size": 48,
                                "fill": "currentColor"
                            },
                            {
                                "name": "arrow-right",
                                "size": 28,
                                "fill": "currentColor"
                            }
                        ],
                        "title": "Discharging"
                        },
                        {
                        "id": "batteryRemainingTime",
                        "icons": [
                            {
                                "name": "clock-history",
                                "size": 48,
                                "fill": "currentColor"
                            },
                            {
                                "name": "arrow-right",
                                "size": 28,
                                "fill": "currentColor"
                            },
                            {
                                "name": "battery",
                                "size": 40,
                                "fill": "currentColor"
                            }
                        ],
                        "title": "Remaining Time"
                        }
                    ]
                }
            ]
        }