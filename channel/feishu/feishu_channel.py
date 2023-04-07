# encoding:utf-8
import json
import hmac
import hashlib
import base64
import time
import requests
from urllib.parse import quote_plus
from common import log
from flask import Flask, request, render_template, make_response
from common import const
from common import functions
from config import channel_conf
from config import channel_conf_val
from channel.channel import Channel
from urllib import request as url_request
from channel.feishu.store import MemoryStore

class FeiShuChannel(Channel):
    def __init__(self):
        self.app_id = channel_conf(
            const.FEISHU).get('app_id')
        self.app_secret = channel_conf(
            const.FEISHU).get('app_secret')
        self.verification_token = channel_conf(
            const.FEISHU).get('verification_token')
        log.info("[FeiShu] app_id={}, app_secret={} verification_token={}".format(
            self.app_id, self.app_secret, self.verification_token))
        self.memory_store = MemoryStore()

    def startup(self):
        http_app.run(host='0.0.0.0', port=channel_conf(
            const.FEISHU).get('port'))
        
    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type": "application/json"
        }
        req_body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = url_request.Request(url=url, data=data,
                              headers=headers, method='POST')
        try:
            response = url_request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return ""

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("get tenant_access_token error, code =", code)
            return ""
        return rsp_dict.get("tenant_access_token", "")

    def notify_feishu(self, token, receive_type, receive_id, at_id, answer):
        log.info("notify_feishu.receive_type = {} receive_id={}",
                 receive_type, receive_id)

        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": receive_type}
        
        # text = at_id and "<at user_id=\"%s\">%s</at>" % (
        #     at_id, answer.lstrip()) or answer.lstrip()
        text = answer.lstrip()
        log.info("notify_feishu.text = {}", text)
        msgContent = {
            "text": text,
        }
        req = {
            "receive_id": receive_id,  # chat id
            "msg_type": "text",
            "content": json.dumps(msgContent),
        }
        payload = json.dumps(req)
        headers = {
            # your access token
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, params=params, headers=headers, data=payload
        )
        log.info("notify_feishu.response.content = {}", response.content)

    def handle(self, message):
        event = message["event"]
        msg = event["message"]
        messageId = msg["message_id"]
        chat_type = msg["chat_type"]
        sender_id = event["sender"]["sender_id"]["open_id"]
        
        prompt = json.loads(msg["content"])["text"]
        prompt = prompt.replace("@_user_1", "")
        
        #重复
        r, v = self.memory_store.get(messageId)
        if v:
            return {'ret': 200}
        
        self.memory_store.set(messageId, True)
        
        # 非文本不处理
        message_type = msg["message_type"]
        if message_type != "text":
            return {'ret': 200}
        if chat_type == "group":
            mentions = msg["mentions"]
            # 日常群沟通要@才生效
            if not mentions:
                return {'ret': 200}
            receive_type = "chat_id"
            receive_id = msg.get("chat_id")
            at_id = sender_id
        elif chat_type == "p2p":
            receive_type = "open_id"
            receive_id = sender_id
            at_id = None

        # 调用发消息 API 之前，先要获取 API 调用凭证：tenant_access_token
        access_token = self.get_tenant_access_token()
        if access_token == "":
            log.error("send message access_token is empty")
            return {'ret': 204}

        context = dict()
        img_match_prefix = functions.check_prefix(
            prompt, channel_conf_val(const.DINGTALK, 'image_create_prefix'))
        if img_match_prefix:
            prompt = prompt.split(img_match_prefix, 1)[1].strip()
            context['type'] = 'IMAGE_CREATE'
        context['from_user_id'] = str(sender_id)
        reply = super().build_reply_content(prompt, context)
        if img_match_prefix:
            if not isinstance(reply, list):
                return {'ret': 204}
            images = ""
            for url in reply:
                images += f"[!['IMAGE_CREATE']({url})]({url})\n"
            reply = images
        # 机器人 echo 收到的消息
        self.notify_feishu(access_token, receive_type,
                           receive_id, at_id, reply)
        return {'ret': 200}

    def handle_request_url_verify(self, post_obj):
        # 原样返回 challenge 字段内容
        challenge = post_obj.get("challenge", "")
        return {'challenge': challenge}


feishu = FeiShuChannel()
http_app = Flask(__name__,)


@http_app.route("/", methods=['POST'])
def chat():
    # log.info("[FeiShu] chat_headers={}".format(str(request.headers)))
    log.info("[FeiShu] chat={}".format(str(request.data)))
    obj = json.loads(request.data)
    if not obj:
        return {'ret': 201}
    # 校验 verification token 是否匹配，token 不匹配说明该回调并非来自开发平台
    headers = obj.get("header")
    if not headers:
        return {'ret': 201}
    token = headers.get("token", "")
    if token != feishu.verification_token:
        log.error("verification token not match, token = {}", token)
        return {'ret': 201}

    # 根据 type 处理不同类型事件
    t = obj.get("type", "")
    if "url_verification" == t:  # 验证请求 URL 是否有效
        return feishu.handle_request_url_verify(obj)
    elif headers.get("event_type", None) == "im.message.receive_v1":  # 事件回调
        return feishu.handle(obj)
    return {'ret': 202}
    
