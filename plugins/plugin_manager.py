# encoding:utf-8
import os
import importlib.util
from plugins.event import EventAction, EventContext,Event
from plugins.plugin_registry import PluginRegistry
from common import functions, log

@functions.singleton
class PluginManager:
    def __init__(self, plugins_dir="./plugins/"):
        self.plugins_dir = plugins_dir
        self.plugin_registry = PluginRegistry()
        self.load_plugins()

    def load_plugins(self):
        for plugin_name in self.find_plugin_names():
            if os.path.exists(f"./plugins/{plugin_name}/{plugin_name}.py"):
                try:
                    plugin_module = self.load_plugin_module(plugin_name)
                    self.plugin_registry.register_from_module(plugin_module)
                except Exception as e:
                    log.warn("Failed to import plugin %s" % (plugin_name))

    def find_plugin_names(self):
        plugin_names = []
        for entry in os.scandir(self.plugins_dir):
            if entry.is_dir():
                plugin_names.append(entry.name)
        return plugin_names

    def load_plugin_module(self, plugin_name):
        spec = importlib.util.spec_from_file_location(
            plugin_name, os.path.join(self.plugins_dir, plugin_name, f"{plugin_name}.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def emit_event(self, e_context: EventContext, *args, **kwargs):
        for plugin in self.plugin_registry.list_plugins():
            if plugin.enabled and e_context.action == EventAction.CONTINUE:
                if(e_context.event in plugin.handlers):
                    plugin.handlers[e_context.event](e_context, *args, **kwargs)
        return e_context
