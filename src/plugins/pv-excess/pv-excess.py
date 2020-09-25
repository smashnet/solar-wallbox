"""
Plugin that reads from a source plugin and calculates if there is excessive power
to route to a consumer plugin
"""
import os
import logging
import plugin_collection

import requests
import struct

log = logging.getLogger("PVExcess")

class PVExcess(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "PV Excess Power"
        self.description = "Read and decode energy data from SENEC Home V3 Hybrid appliances."
        self.type = "switcher"
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.settings = { # Will be read from src/config/settings.json
            "plugin_path": "/excess"
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
        res = {}
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
            "excessPower": 0.0   # Excess power (in W)
        }
        """
        try:
            data = self.source.getData()
        except:
            data = {
                "PVProduction": 3000.0,
                "housePower": 1432.3,
                "batteryChargeRate": 844.2
            }
        return {
            "excessPower": data['PVProduction'] - data['housePower'] - data['batteryChargeRate']
        }


    def __send_response(self, res_web, resp, template_vars):
        template_vars['res'] = res_web
        resp.html = self.webserver.render_template("pv-excess/index.html", template_vars)

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __get_web_dict(self):
        return {
            "cards": [
                [
                    {
                    "id": "excessPower",
                    "icons": [
                        {
                            "name": "lightning",
                            "size": 48,
                            "fill": "currentColor"
                        }
                    ],
                    "title": "PV-Überschuss"
                    }
                ]
            ]
        }