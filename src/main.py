import sys
import time

import logging
import responder

from web_server import WebServer
from plugin_collection import PluginCollection

logging.basicConfig(level=logging.NOTSET)
log = logging.getLogger("Main")

if __name__ == "__main__":
    settings = {
        "common": {
            "pluginsPackage": "plugins",
            "templates": "./templates",
            "static-assets": "./static-assets"
        },
        "web": {
            "address": "0.0.0.0",
            "port": 8080
        }
    }

    # Create plugin collection with all plugins found in the plugins folder
    # and install assets
    plugin_collection = PluginCollection(
        settings['common']['pluginsPackage'],
        settings['common']['static-assets'],
        settings['common']['templates']
        )

    # Apply settings to plugins. There must be a top level key in the
    # settings dict named after the plugin class. Otherwise, the plugin
    # default settings will be used.
    plugin_collection.apply_settings(settings)

    try:
        WebServer(settings, plugin_collection).run()
    except KeyboardInterrupt:
        log.info("Bye bye!")