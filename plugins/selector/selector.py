# encoding:utf-8

import os
import plugins
from plugins import *
from common import log
from common import functions


@plugins.register(name="Selector", desire_priority=99, hidden=True, desc="A model selector", version="0.1", author="RegimenArsenic")
class Selector(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        try:
            self.config = functions.load_json_file(curdir, "selector.json")
        except Exception as e:
            log.warn("[Selector] init failed")
            raise e
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.select_model
        self.handlers[Event.ON_BRIDGE_HANDLE_STREAM_CONTEXT] = self.select_model
        log.info("[Selector] inited")

    def get_events(self):
        return self.handlers

    def select_model(self, e_context: EventContext):
        model=e_context['args'].get('model')
        for selector in self.config.get("selector", []):
            prefix = selector.get('prefix', [])
            check_prefix=functions.check_prefix(e_context["context"], prefix)
            if (check_prefix):
                model=selector.get('model')
                if isinstance(check_prefix, str):
                    e_context["context"] = e_context["context"].split(check_prefix, 1)[1].strip()
                break
        log.debug(f"[Selector] select model {model}")
        e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
        e_context['args']['model']=model
        return e_context
