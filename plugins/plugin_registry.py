# encoding:utf-8

import inspect
from plugins.plugin import Plugin
from common.log import logger
from common import functions

@functions.singleton
class PluginRegistry:
    def __init__(self):
        self.plugins = []

    def register(self, name: str, desire_priority: int = 0, **kwargs):
        def wrapper(plugin_cls):
            plugin_cls.name = name
            plugin_cls.priority = desire_priority
            plugin_cls.desc = kwargs.get('desc')
            plugin_cls.author = kwargs.get('author')
            plugin_cls.version = kwargs.get('version') or "1.0"
            plugin_cls.namecn = kwargs.get('namecn') or name
            plugin_cls.hidden = kwargs.get('hidden') or False
            plugin_cls.enabled = kwargs.get('enabled') or True
            logger.info(f"Plugin {name}_v{plugin_cls.version} registered")
            return plugin_cls
        return wrapper

    def register_from_module(self, module):
            plugins = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                    plugin_name = getattr(obj, "name", None)
                    if plugin_name:
                        plugin = obj()
                        plugin.name = plugin_name
                        plugin.priority = getattr(obj, "priority", 0)
                        plugin.desc = getattr(obj, "desc", None)
                        plugin.author = getattr(obj, "author", None)
                        plugin.version = getattr(obj, "version", "1.0")
                        plugin.namecn = getattr(obj, "namecn", plugin_name)
                        plugin.hidden = getattr(obj, "hidden", False)
                        plugin.enabled = getattr(obj, "enabled", True)
            # Sort the list of plugins by priority
            self.plugins.append(plugin)
            self.plugins.sort(key=lambda x: x.priority, reverse=True)

    def get_plugin(self, name):
        plugin = next((p for p in self.plugins if p.name.upper() == name.upper()), None)
        return plugin

    def list_plugins(self):
        return [plugin for plugin in self.plugins]