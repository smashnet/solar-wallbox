import sys
import time

import json
import logging
import responder

from web_server import WebServer
from plugin_collection import PluginCollection

logging.basicConfig(level=logging.NOTSET)
log = logging.getLogger("Main")

if __name__ == "__main__":
    # Load config from file
    try:
        with open('config/settings.json', 'r') as settings_file:
            data = settings_file.read()
        settings = json.loads(data)
    except EnvironmentError:
        log.error("Could not open src/config/settings.json")
        log.error("Please fill in sample_settings.json to your needs and copy to src/config/settings.json or to your config volume!")
        sys.exit("Could not open settings.json")

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