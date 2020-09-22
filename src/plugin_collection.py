import inspect
import os
import shutil
import errno
import pkgutil
import logging

"""
Greatfully taken from: https://github.com/gdiepen/python_plugin_example
"""

log = logging.getLogger("PluginCollection")

class Plugin(object):
    """Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    def __init__(self):
        self.description = 'UNKNOWN'

    def perform_operation(self, argument):
        """The method that we expect all plugins to implement. This is the
        method that our framework will call
        """
        raise NotImplementedError


class PluginCollection(object):
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_package, assets_dir, templates_dir):
        """Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created
        """
        self.plugin_package = plugin_package
        self.assets_destination_dir = assets_dir
        self.templates_destination_dir = templates_dir
        self.reload_plugins()


    def reload_plugins(self):
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        self.plugins = []
        self.seen_paths = []
        log.info(f' Looking for plugins under package {self.plugin_package}')
        self.walk_package(self.plugin_package)
        log.info(f' ... done!')
        self.install_plugin_frontends()

    def apply_settings(self, settings):
        for plugin in self.plugins:
            plugin.apply_settings(settings)

    def list_plugins(self):
        """Output a list of the plugin names
        """
        return [(type(plugin).__name__, plugin.title, plugin.settings['plugin_path']) for plugin in self.plugins]

    def get_plugins(self):
        """Return plugins
        """
        return self.plugins

    def get_plugin(self, plugin_name):
        """Returns the plugin specified by this name
        """
        for plugin in self.plugins:
            if(plugin_name == type(plugin).__name__):
                return plugin

    def apply_plugin_on_value(self, plugin_name, argument):
        """Apply specific plugin on the argument supplied to this function
        """
        for plugin in self.plugins:
            if(plugin_name == type(plugin).__name__):
                log.debug(f"Plugin {plugin_name} found. Executing!")
                return plugin.perform_operation(argument)
            else:
                log.debug(f"Plugin {plugin_name} not found :-(")


    def apply_all_plugins_on_value(self, argument):
        """Apply all of the plugins on the argument supplied to this function
        """
        for plugin in self.plugins:
            plugin.perform_operation(argument)

    def install_plugin_frontends(self):
        """Look if plugins have frontends and tem and install them
            - Static assets in: assets_destination_dir + "/{pluginname}/"
            - Templates in: templates_destination_dir + "/{pluginname}/"
        """
        log.info(f' Installing plugin assets...')
        for plugin in self.plugins:
            plugin_folder = type(plugin).__module__.split('.')[1]
            # Check if plugin has "assets" folder, and copy
            source_dir = f"./{self.plugin_package}/{plugin_folder}/assets"
            dest_dir = f"{self.assets_destination_dir}/{plugin_folder}/"
            # Clear destination folder
            shutil.rmtree(dest_dir, ignore_errors=True)
            if os.path.isdir(source_dir):
                log.debug(f" Copy assets for plugin {type(plugin).__name__}")
                log.debug(f"    from: {source_dir}")
                log.debug(f"    to  : {dest_dir}")
                self.copy(source_dir, dest_dir)
            
            # Check if plugin has "templates" folder, and copy
            source_dir = f"./{self.plugin_package}/{plugin_folder}/templates"
            dest_dir = f"{self.templates_destination_dir}/{plugin_folder}/"
            # Clear destination folder
            shutil.rmtree(dest_dir, ignore_errors=True)
            if os.path.isdir(source_dir):
                log.debug(f" Copy templates for plugin {type(plugin).__name__}")
                log.debug(f"    from: {source_dir}")
                log.debug(f"    to  : {dest_dir}")
                self.copy(source_dir, dest_dir)
        log.info(f' ... done!')

    def walk_package(self, package):
        """Recursively walk the supplied package to retrieve all plugins
        """
        imported_package = __import__(package, fromlist=['blah'])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['blah'])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in clsmembers:
                    # Only add classes that are a sub class of Plugin, but NOT Plugin itself
                    if issubclass(c, Plugin) & (c is not Plugin):
                        log.info(f'    Found plugin class: {c.__module__}.{c.__name__}')
                        self.plugins.append(c())


        # Now that we have looked at all the modules in the current package, start looking
        # recursively for additional modules in sub packages
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # Get all sub directory of the current package path directory
                child_pkgs = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]

                # For each sub directory, apply the walk_package method recursively
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)

    def copy(self, src, dest):
        try:
            shutil.copytree(src, dest)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(src, dest)
            else:
                log.error('Directory not copied. Error: %s' % e)