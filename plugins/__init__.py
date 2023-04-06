# encoding:utf-8
from .event import *
from .plugin import *
from plugins.plugin_registry import PluginRegistry

instance = PluginRegistry()

register                    = instance.register
# load_plugins                = instance.load_plugins
# emit_event                  = instance.emit_event
