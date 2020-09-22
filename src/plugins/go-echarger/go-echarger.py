"""
Read and decode data from go-eCharger wallbox.
"""
import os
import logging
import plugin_collection

log = logging.getLogger("GoEcharger")

class GoEcharger(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "go-eCharger"
        self.description = "Read and decode data from go-eCharger wallbox."
        self.settings = { # defaults
            "url": "/goe"
        }

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")

    def endpoint(self, req, resp):
        resp.html = "go-eCharger"

    def perform_operation(self, event):
        return("Success!")

    def on_success_callback(self, res):
        print(f"Success callback: {res}")

    def on_error_callback(self, res):
        print(f"Error callback: {res}")