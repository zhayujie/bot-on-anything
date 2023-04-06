# encoding:utf-8

from channel.http.http_channel import HttpChannel
from channel.wechat.wechat_channel import WechatChannel
import plugins
from plugins import *
from common import functions
from config import channel_conf
from config import channel_conf_val
from common import const


@plugins.register(name="CreateImg", desire_priority=90, hidden=True, desc="A simple plugin that create images from model", version="0.1", author="RegimenArseic")
class Createimg(Plugin):
    def __init__(self):
        super().__init__()
        self.handles = {HttpChannel: self.handle_http}
        self.channel_types = {HttpChannel: const.HTTP,
                              WechatChannel: const.WECHAT}
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.handle_query
        self.handlers[Event.ON_DECORATE_REPLY] = self.send_images

    def get_events(self):
        return self.handlers

    def handle_query(self, e_context: EventContext):
        channel = e_context['channel']
        channel_type = self.channel_types.get(type(channel), None)
        if (channel_type):
            query = e_context['context']
            if (query):
                img_match_prefix = functions.check_prefix(
                    query, channel_conf_val(channel_type, 'image_create_prefix'))
                if img_match_prefix:
                    if (channel_type == const.HTTP) and e_context['args'].get('stream', False):
                        e_context['reply'] = channel.handle(
                            {'msg': e_context['args']['origin'], 'id': e_context['args']['from_user_id']})
                        e_context.action = EventAction.BREAK_PASS
                    else:
                        query = query.split(img_match_prefix, 1)[1].strip()
                        e_context['args']['type'] = 'IMAGE_CREATE'
                        if (channel_type == const.WECHAT):
                            channel._do_send_img(
                                query, e_context['args'])
                            e_context.action = EventAction.BREAK_PASS
                        else:
                            e_context.action = EventAction.CONTINUE
        return e_context

    def handle_http(self, e_context: EventContext):
        reply = e_context["reply"]
        if e_context['args'].get('type', '') == 'IMAGE_CREATE':
            if isinstance(reply, list):
                images = ""
                for url in reply:
                    images += f"[!['IMAGE_CREATE']({url})]({url})\n\n"
            e_context["reply"] = images
        return e_context

    def send_images(self, e_context: EventContext):
        channel = e_context['channel']
        method = self.handles.get(type(channel), None)
        if (method):
            e_context = method(e_context)
        e_context.action = EventAction.BREAK_PASS  # 事件结束，不再给下个插件处理，不交付给默认的事件处理逻辑
        return e_context
