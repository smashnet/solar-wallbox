"""
Plugin that reads from a source plugin and calculates if there is excessive power
to route to a consumer plugin
"""
import os
import time
import logging
import plugin_collection

import requests
import struct

log = logging.getLogger("PVExcess")

class PVExcess(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "PV Excess Power"
        self.description = "Permanently monitors SENEC plugin and switches wallbox accordingly."
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "switch"
        self.has_runtime = True
        self.settings = { # Will be read from src/config/settings.json
            "plugin_path": "/excess"
        }
        self.excess = 0.0

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")

    def runtime(self, other_plugins):
        (source_plugin, consumer_plugin) = self.__find_source_and_consumer_plugins(other_plugins)
        # PVExcess needs exactly one source-plugin (self.type = "source"), and one consumer-plugin (self.type = "consumer")
        if not source_plugin:
            log.error("No power source plugin found!")
            return
        if not consumer_plugin:
            log.error("No consumer plugin found!")
            return
        # This is run permanently in the background
        while True:
            data = source_plugin.getData()
            try:
                self.excess = {"excessPower": data['live_data']['pv_production'] - data['live_data']['house_power'] - data['live_data']['battery_charge_power']}
            except KeyError:
                pass

            time.sleep(2)

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
        return self.excess

    def __find_source_and_consumer_plugins(self, other_plugins):
        source_plugin = False
        consumer_plugin = False
        for plugin in other_plugins:
            if plugin.type == "source":
                source_plugin = plugin
            if plugin.type == "consumer":
                consumer_plugin = plugin
        return (source_plugin, consumer_plugin)

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
                    "title": "Excess Power"
                    }
                ]
            ]
        }