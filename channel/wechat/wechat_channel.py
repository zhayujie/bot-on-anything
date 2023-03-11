# encoding:utf-8

"""
wechat channel
"""

import itchat
import json
from itchat.content import *
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from common import const
from config import channel_conf_val, channel_conf
import requests
from urllib.parse import urlencode, quote

from common.sensitive_word import SensitiveWord

import io


thread_pool = ThreadPoolExecutor(max_workers=8)



sw = SensitiveWord()

# ...


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group(msg)
    return None





class WechatChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2)

        # start message listener
        itchat.run()




    def handle(self, msg):
        logger.debug("[WX]receive msg: " + json.dumps(msg, ensure_ascii=False))
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']              # 接收人id
        other_user_id = msg['User']['UserName']     # 对手方id
        content = msg['Text']

        # 调用敏感词检测函数
        if sw.process_text(content):
            self.send('请注意文明用语', from_user_id)
            return

        match_prefix = self.check_prefix(content, channel_conf_val(const.WECHAT, 'single_chat_prefix'))
        if from_user_id == other_user_id and match_prefix is not None:
            # 好友向自己发送消息
            if match_prefix != '':
                str_list = content.split(match_prefix, 1)
                if len(str_list) == 2:
                    content = str_list[1].strip()

            img_match_prefix = self.check_prefix(content, channel_conf_val(const.WECHAT, 'image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, from_user_id)
            else:
                thread_pool.submit(self._do_send, content, from_user_id)

        elif to_user_id == other_user_id and match_prefix:
            # 自己给好友发送消息
            str_list = content.split(match_prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()
            img_match_prefix = self.check_prefix(content, channel_conf_val(const.WECHAT, 'image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, to_user_id)
            else:
                thread_pool.submit(self._do_send, content, to_user_id)


    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        if not group_name:
            return None
        origin_content = msg['Content']
        content = msg['Content']
        content_list = content.split(' ', 1)
        context_special_list = content.split('\u2005', 1)
        if len(context_special_list) == 2:
            content = context_special_list[1]
        elif len(content_list) == 2:
            content = content_list[1]

        # 调用敏感词检测函数
        if sw.process_text(content):
            self.send('请注意文明用语', group_id)
            return

        match_prefix = (msg['IsAt'] and not channel_conf_val(const.WECHAT, "group_at_off", False)) or self.check_prefix(origin_content, channel_conf_val(const.WECHAT, 'group_chat_prefix')) or self.check_contain(origin_content, channel_conf_val(const.WECHAT, 'group_chat_keyword'))

        group_white_list = channel_conf_val(const.WECHAT, 'group_name_white_list')
        
        if ('ALL_GROUP' in group_white_list or group_name in group_white_list or self.check_contain(group_name, channel_conf_val(const.WECHAT, 'group_name_keyword_white_list'))) and match_prefix:

            img_match_prefix = self.check_prefix(content, channel_conf_val(const.WECHAT, 'image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, group_id)
            else:
                thread_pool.submit(self._do_send_group, content, msg)
        return None

    def send(self, msg, receiver):
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))
        itchat.send(msg, toUserName=receiver)

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                self.send(channel_conf_val(const.WECHAT, "single_chat_reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            logger.exception(e)

    def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return

            # 图片下载
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)

            # 图片发送
            logger.info('[WX] sendImage, receiver={}'.format(reply_user_id))
            itchat.send_image(image_storage, reply_user_id)
        except Exception as e:
            logger.exception(e)

    def _do_send_group(self, query, msg):
        if not query:
            return
        context = dict()
        context['from_user_id'] = msg['ActualUserName']
        reply_text = super().build_reply_content(query, context)
        if reply_text:
            reply_text = '@' + msg['ActualNickName'] + ' ' + reply_text.strip()
            self.send(channel_conf_val(const.WECHAT, "group_chat_reply_prefix", "") + reply_text, msg['User']['UserName'])


    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None


    def check_contain(self, content, keyword_list):
        if not keyword_list:
            return None
        for ky in keyword_list:
            if content.find(ky) != -1:
                return True
        return None
    

'''
这是一个基于itchat库的微信机器人实现，支持单聊和群聊消息的自动回复和图片发送等功能。代码中使用了线程池技术和异步回调函数等方式来提高程序的性能和并发处理能力。

其中，WechatChannel 类实现了 Channel 接口，并定义了一些额外的方法，如发送消息、检测敏感词汇、处理单聊和群聊消息等。

send() 函数用于向指定用户发送文本消息；
_do_send() 函数用于处理接收到的文本消息并回复相应的内容；
_do_send_img() 函数用于处理接收到的图片消息并发送相应的图片内容；
_do_send_group() 函数用于处理接收到的群组消息并回复相应的内容；

check_prefix() 函数用于检查消息是否以指定前缀开头；
check_contain() 函数用于检查消息是否包含指定关键字。

handler_single_msg() 函数和 handler_group_msg() 函数分别用于处理接收到的单聊和群聊消息，并回复相应的内容。

在handle() 函数中，先根据消息类型和内容进行分类和处理，然后利用线程池并发处理多个消息，提高程序的处理效率。

整体上来说，这段代码实现了一个简单的微信机器人，并且具有较好的可扩展性，可以通过增加不同的处理函数或者修改匹配规则等方式来实现更为丰富的功能。
'''


