"""
Read and decode energy data from SENEC Home V3 Hybrid appliances.
"""
import os
import logging
import plugin_collection

import requests
import struct

log = logging.getLogger("Senec")

class SenecHomeV3Hybrid(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "SENEC.Home V3 hybrid (duo)"
        self.description = "Read and decode energy data from SENEC Home V3 Hybrid appliances."
        self.type = "source"
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.settings = { # Will be read from src/config/settings.json
            "plugin_path": "/senec",
            "device_ip": "IP_OF_YOUR_SENEC_DEVICE",
            "device_api_path": "/lala.cgi",
            "batteryCapacity": 10 # in kWh
        }

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")

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
        getData can be used by other plugins. Values delivered are:
        {
            "housePower": 0.0,              # Power used (in W)
            "PVProduction": 0.0,            # Power produced by PV (in W)
            "batteryChargeRate": 0.0,       # The battery charging rate (in W)
            "batteryDischargeRate": 0.0,    # The battery discharging rate (in W)
            "batteryPercentage": 0.0,       # Remaining battery in percent
            "batteryCapacity": 10,          # Battery capacity in kWh
            "gridPull": 0.0,                # Power pulled from public grid (in W)
            "gridPush": 0.0                 # Power pushed to public grid (in W)
        }
        """
        from_appliance = self.__request_data_from_senec_appliance()
        if from_appliance.status_code == 200:
            decoded = self.__decode_data(from_appliance.json())
            res = {
                "housePower": decoded['ENERGY']['GUI_HOUSE_POW'],
                "PVProduction": decoded['ENERGY']['GUI_INVERTER_POWER'],
                "batteryChargeRate": 0.0,
                "batteryDischargeRate": 0.0,
                "batteryPercentage": decoded['ENERGY']['GUI_BAT_DATA_FUEL_CHARGE'],
                "batteryCapacity": self.settings['batteryCapacity'],
                "gridPull": 0.0,
                "gridPush": 0.0
                }
            if decoded['ENERGY']['GUI_BAT_DATA_POWER'] > 0:
                res['batteryChargeRate'] = decoded['ENERGY']['GUI_BAT_DATA_POWER']
            else:
                res['batteryDischargeRate'] = decoded['ENERGY']['GUI_BAT_DATA_POWER'] * -1
            
            if decoded['ENERGY']['GUI_GRID_POW'] > 0:
                res['gridPull'] = decoded['ENERGY']['GUI_GRID_POW']
            else:
                res['gridPush'] = decoded['ENERGY']['GUI_GRID_POW'] * -1
            return res


    def __send_response(self, res_web, resp, template_vars):
        template_vars['res'] = res_web
        resp.html = self.webserver.render_template("senec/index.html", template_vars)

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __decode_data(self, data):
        for item in data['ENERGY']:
            data['ENERGY'][item] = self.__decode_value(data['ENERGY'][item])
        return data

    def __decode_value(self, value):
        if value.startswith("fl_"):
            return struct.unpack('!f', bytes.fromhex(value[3:]))[0]
        if value.startswith("u8_"):
            return struct.unpack('!B', bytes.fromhex(value[3:]))[0]
        return value

    '''
    {
    "ENERGY":
        {"STAT_STATE":"","STAT_STATE_DECODE":"","GUI_BAT_DATA_POWER":"","GUI_INVERTER_POWER":"",
        "GUI_HOUSE_POW":"","GUI_GRID_POW":"","STAT_MAINT_REQUIRED":"","GUI_BAT_DATA_FUEL_CHARGE":"",
        "GUI_CHARGING_INFO":"","GUI_BOOSTING_INFO":""},
    "WIZARD":
        {"CONFIG_LOADED":"","SETUP_NUMBER_WALLBOXES":"","SETUP_WALLBOX_SERIAL0":"",
        "SETUP_WALLBOX_SERIAL1":"","SETUP_WALLBOX_SERIAL2":"","SETUP_WALLBOX_SERIAL3":""},
    "SYS_UPDATE":
        {"UPDATE_AVAILABLE":""}
    }
    '''
    def __request_data_from_senec_appliance(self):
        return requests.post("http://" + self.settings['device_ip'] + self.settings['device_api_path'], json={
            "ENERGY":
                {"STAT_STATE":"","STAT_STATE_DECODE":"","GUI_BAT_DATA_POWER":"","GUI_INVERTER_POWER":"",
                "GUI_HOUSE_POW":"","GUI_GRID_POW":"","STAT_MAINT_REQUIRED":"","GUI_BAT_DATA_FUEL_CHARGE":"",
                "GUI_CHARGING_INFO":"","GUI_BOOSTING_INFO":""}})

    def __get_web_dict(self):
        return {
            "cards": [
                [
                    {
                    "id": "housePower",
                    "icons": [
                        {
                            "name": "house",
                            "size": 48,
                            "fill": "currentColor"
                        }
                    ],
                    "title": "Hausverbrauch"
                    },
                    {
                    "id": "inverterPower",
                    "icons": [
                        {
                            "name": "sun",
                            "size": 48,
                            "fill": "currentColor"
                        }
                    ],
                    "title": "PV-Erzeugung"
                    }
                ],[
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
                    "title": "Akku-Beladung"
                    },
                    {
                    "id": "batteryDischarge",
                    "icons": [
                        {
                            "name": "battery-charging",
                            "size": 48,
                            "fill": "currentColor"
                        },
                        {
                            "name": "arrow-right",
                            "size": 28,
                            "fill": "currentColor"
                        }
                    ],
                    "title": "Akku-Entnahme"
                    }
                ],[
                    {
                    "id": "gridPull",
                    "icons": [
                        {
                            "name": "lightning",
                            "size": 48,
                            "fill": "currentColor"
                        },
                        {
                            "name": "arrow-right",
                            "size": 28,
                            "fill": "currentColor"
                        }
                    ],
                    "title": "Netzbezug"
                    },
                    {
                    "id": "gridPush",
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
                    ],
                    "title": "Netzeinspeisung"
                    }
                ],[
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
                    "title": "Akku-Restlaufzeit"
                    }
                ]
            ]
        }