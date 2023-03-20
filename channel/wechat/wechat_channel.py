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
from config import channel_conf_val
import requests

from common.sensitive_word import SensitiveWord

import io


thread_pool = ThreadPoolExecutor(max_workers=8)
sw = SensitiveWord()

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
        itchat.auto_login(enableCmdQR=2, hotReload=True)

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
            self.send('请检查您的输入是否有违规内容', from_user_id)
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

        

        match_prefix = (msg['IsAt'] and not channel_conf_val(const.WECHAT, "group_at_off", False)) or self.check_prefix(origin_content, channel_conf_val(const.WECHAT, 'group_chat_prefix')) or self.check_contain(origin_content, channel_conf_val(const.WECHAT, 'group_chat_keyword'))

        # 如果在群里被at了 或 触发机器人关键字，则调用敏感词检测函数
        if match_prefix is True:
            if sw.process_text(content):
                self.send('请检查您的输入是否有违规内容', group_id)
                return

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
