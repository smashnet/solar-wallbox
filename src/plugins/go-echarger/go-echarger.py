"""
Read and write data of go-eCharger wallbox.
"""
import os
import logging
import plugin_collection

log = logging.getLogger("GoEcharger")

class GoEcharger(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "go-eCharger"
        self.description = "Read and write data of go-eCharger wallbox."
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.settings = { # defaults
            "plugin_path": "/go-echarger",
            "device_ip": "10.0.0.47",
            "device_api_path": "/status"
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
        resp.html = self.webserver.render_template("go-echarger/index.html", template_vars)