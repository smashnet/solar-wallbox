import responder
import datetime
import logging
import threading

log = logging.getLogger("WebServer")

class WebServer:
    def __init__(self, settings, plugins):
        self.api = responder.API(
            title="Solar Wallbox",
            version="0.0.1",
            description="See and control your energy data and control your wallbox.",
            static_dir=settings["common"]["static-assets"],
            templates_dir=settings["common"]["templates"]
            )
        self.address = settings["web"]["address"]
        self.port = settings["web"]["port"]
        self.plugins = plugins
        self.__register_routes()
        self.__start_plugin_runtimes()

    def __register_routes(self):
        self.api.add_route("/", endpoint=self.__list_plugins)
        for plugin in self.plugins.get_plugins():
            plugin.add_webserver(self)
            self.api.add_route(plugin.settings['plugin_path'], endpoint=plugin.endpoint)

    def __start_plugin_runtimes(self):
        log.info("Starting plugin runtimes...")
        for plugin in self.plugins.get_plugins():
            if plugin.has_runtime:
                plugin_runtime_thread = threading.Thread(target=plugin.runtime, args=(self.plugins,), daemon=True)
                plugin_runtime_thread.start()

    def render_template(self, path, template_vars=None):
        template_vars = template_vars if template_vars else {}
        now = datetime.datetime.now()
        template_vars['currentYear'] = now.year
        return self.api.template(path, vars=template_vars)

    #@staticmethod
    def __list_plugins(self, req, resp):
        template_vars = {
            "pluginPackage": "home"
        }
        template_vars['res'] = self.__get_web_dict(self.plugins.list_plugins())
        resp.html = self.render_template("home/index.html", template_vars)

    def run(self):
        self.api.run(address=self.address, port=self.port)

    def __get_web_dict(self, plugins):
        res = {
            "cards": []
        }
        for (name, title, href) in plugins:
            res['cards'].append(
                {
                    "id": name,
                    "icons": [
                        {
                            "name": "sticky",
                            "size": 48,
                            "fill": "currentColor"
                        }
                    ],
                    "title": title,
                    "href": href
                }
            )
        return res