"""
Read and decode energy data from SENEC Home V3 Hybrid appliances.
"""
import os
import schedule
import time
import logging

import plugin_collection

log = logging.getLogger("Dashboard")

class Dashboard(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "Solar Dashboard"
        self.description = "Overview over SENEC and go-E"
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "sink"
        self.has_runtime = True
        self.current_data = {}
        self.settings = {}

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]

    def runtime(self, other_plugins):
        # This is run permanently in the background
        while True:
            senec = other_plugins.get_plugin("SenecHomeV3Hybrid")
            goe = other_plugins.get_plugin("GoEcharger")
            self.current_data = {
                "house": senec.get_data(),
                "wallbox1": goe.get_data(0),
                "wallbox2": goe.get_data(1)
            }
            time.sleep(2)

    def endpoint(self, req, resp):
        viewmodel = self.__create_view_model(req)
        if (self.__get_output_format(req) == "json"):
            res = self.current_data
            resp.media = res
            return
        resp.html = self.webserver.render_template("dashboard/index.html", viewmodel)

    def __create_view_model(self, req):
        # Path: plugin_path + /
        return {
            "pluginPackage": self.pluginPackage,
            "name": type(self).__name__,
            "structure": self.__get_web_dict()
        }

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
                    "title": "Production and Storage",
                    "blocks": [
                        {
                            "id": "pvProduction",
                            "title": "Production",
                            "type": "square",
                            "icons": [
                                {"name": "sun", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "gridPower",
                            "title": "Grid Power",
                            "type": "square",
                            "icons": [
                                {"name": "lightning", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "batteryPower",
                            "title": "Battery Power",
                            "type": "square_wide",
                            "icons": [
                                {"name": "battery-full", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Consumers",
                    "blocks": [
                        {
                            "id": "housePower",
                            "title": "House",
                            "type": "square_wide",
                            "icons": [
                                {"name": "house", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "wallbox1",
                            "switch_id": "wallbox1_switch",
                            "title": "Wallbox Parkplatz",
                            "type": "square_onoff",
                            "icons": [
                                {"name": "plug", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "wallbox2",
                            "switch_id": "wallbox2_switch",
                            "title": "Wallbox Garage",
                            "type": "square_onoff",
                            "icons": [
                                {"name": "plug", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                }
            ]
        }