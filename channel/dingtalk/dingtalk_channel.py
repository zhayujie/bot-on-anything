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


class DingTalkHandler():
    def __init__(self, config):
        self.dingtalk_key = config.get('dingtalk_key')
        self.dingtalk_secret = config.get('dingtalk_secret')
        self.dingtalk_token = config.get('dingtalk_token')
        self.dingtalk_post_token = config.get('dingtalk_post_token')
        self.access_token = None
        log.info("[DingTalk] AppKey={}, AppSecret={} Token={} post Token={}".format(self.dingtalk_key, self.dingtalk_secret, self.dingtalk_token, self.dingtalk_post_token))

    def notify_dingtalk_webhook(self, data):
        timestamp = round(time.time() * 1000)
        secret_enc = bytes(self.dingtalk_secret, encoding='utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.dingtalk_secret)
        string_to_sign_enc = bytes(string_to_sign, encoding='utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc,
                             digestmod=hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(hmac_code))

        notify_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dingtalk_token}&timestamp={timestamp}&sign={sign}"
        try:
            log.info("[DingTalk] url={}".format(str(notify_url)))
            r = requests.post(notify_url, json=data)
            reply = r.json()
            log.info("[DingTalk] reply={}".format(str(reply)))
        except Exception as e:
            log.error(e)

    def get_token_internal(self):
        access_token_url = 'https://api.dingtalk.com/v1.0/oauth2/accessToken'
        try:
            r = requests.post(access_token_url, json={"appKey": self.dingtalk_key, "appSecret": self.dingtalk_secret})
        except:
            raise Exception("DingTalk token获取失败!!!")

        data = json.loads(r.content)
        access_token = data['accessToken']
        expire_in = data['expireIn']
        
        self.access_token = access_token
        self.expire_at = int(expire_in) + time.time()

        return self.access_token
    
    def get_token(self):
        if self.access_token is None or self.expire_at <= time.time():
            self.get_token_internal()
        
        return self.access_token
    
    def get_post_url(self, data):
        type = data['conversationType']
        if type == "1":
            return f"https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
        else:
            return f"https://api.dingtalk.com/v1.0/robot/groupMessages/send"
    
    def build_response(self, reply, data):
        type = data['conversationType']
        if type == "1":
            return self.build_oto_response(reply, data)
        else:
            return self.build_group_response(reply, data)

    def build_oto_response(self, reply, data):
        conversation_id = data['conversationId']
        prompt = data['text']['content']
        prompt = prompt.strip()
        img_match_prefix = functions.check_prefix(
            prompt, channel_conf_val(const.DINGTALK, 'image_create_prefix'))
        nick = data['senderNick']
        staffid = data['senderStaffId']
        robotCode = data['robotCode']
        if img_match_prefix and isinstance(reply, list):
            images = ""
            for url in reply:
                images += f"!['IMAGE_CREATE']({url})\n"
            reply = images
            resp = {
                "msgKey": "sampleMarkdown",
                "msgParam": json.dumps({
                    "title": "IMAGE @" + nick + " ", 
                    "text": images + " \n " + "@" + nick
                }),
                "robotCode": robotCode,
                "userIds": [staffid]
            }
        else:
            resp = {
                "msgKey": "sampleText",
                "msgParam": json.dumps({
                    "content": reply
                }),
                "robotCode": robotCode,
                "userIds": [staffid]
            }
        return resp
    
    def build_group_response(self, reply, data):
        conversation_id = data['conversationId']
        prompt = data['text']['content']
        prompt = prompt.strip()
        img_match_prefix = functions.check_prefix(
            prompt, channel_conf_val(const.DINGTALK, 'image_create_prefix'))
        nick = data['senderNick']
        staffid = data['senderStaffId']
        robot_code = data['robotCode']
        if img_match_prefix and isinstance(reply, list):
            images = ""
            for url in reply:
                images += f"!['IMAGE_CREATE']({url})\n"
            reply = images
            resp = {
                "msgKey": "sampleMarkdown",
                "msgParam": json.dumps({
                    "title": "IMAGE @" + nick + " ", 
                    "text": images + " \n " + "@" + nick
                }),
                "robotCode": robot_code,
                "openConversationId": conversation_id,
                "at": {
                    "atUserIds": [
                        staffid
                    ],
                    "isAtAll": False
                }
            }
        else:
            resp = {
                "msgKey": "sampleText",
                "msgParam": json.dumps({
                    "content": reply + " \n " + "@" + nick
                }),
                "robotCode": robot_code,
                "openConversationId": conversation_id,
                "at": {
                    "atUserIds": [
                       staffid 
                    ],
                    "isAtAll": False
                }
            }
        return resp
    
    
    def build_webhook_response(self, reply, data):
        conversation_id = data['conversationId']
        prompt = data['text']['content']
        prompt = prompt.strip()
        img_match_prefix = functions.check_prefix(
            prompt, channel_conf_val(const.DINGTALK, 'image_create_prefix'))
        nick = data['senderNick']
        staffid = data['senderStaffId']
        robotCode = data['robotCode']
        if img_match_prefix and isinstance(reply, list):
            images = ""
            for url in reply:
                images += f"!['IMAGE_CREATE']({url})\n"
            reply = images
            resp = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "IMAGE @" + nick + " ", 
                    "text": images + " \n " + "@" + nick
                },
                "at": {
                    "atUserIds": [
                        staffid
                    ],
                    "isAtAll": False
                }
            }
        else:
            resp = {
                "msgtype": "text",
                "text": {
                    "content": reply
                },
                "at": {
                    "atUserIds": [
                       staffid 
                    ],
                    "isAtAll": False
                }
            }
        return resp
    
    def chat(self, channel, data):
        reply = channel.handle(data)
        type = data['conversationType']
        if type == "1":
            reply_json = self.build_response(reply, data)
            self.notify_dingtalk(data, reply_json)
        else:
            # group的不清楚怎么@，先用webhook调用
            reply_json = self.build_webhook_response(reply, data)
            self.notify_dingtalk_webhook(reply_json)
        

    def notify_dingtalk(self, data, reply_json):
        headers = {
            'content-type': 'application/json', 
            'x-acs-dingtalk-access-token': self.get_token()
        }

        notify_url = self.get_post_url(data)
        try:
            r = requests.post(notify_url, json=reply_json, headers=headers)
            resp = r.json()
            log.info("[DingTalk] response={}".format(str(resp)))
        except Exception as e:
            log.error(e)


class DingTalkChannel(Channel):
    def __init__(self):
        log.info("[DingTalk] started.")

    def startup(self):
        http_app.run(host='0.0.0.0', port=channel_conf(const.DINGTALK).get('port'))

    def handle(self, data):
        reply = "您好，有什么我可以帮助您解答的问题吗？"
        prompt = data['text']['content']
        prompt = prompt.strip()
        if str(prompt) != 0:
            conversation_id = data['conversationId']
            sender_id = data['senderId']
            context = dict()
            img_match_prefix = functions.check_prefix(
                prompt, channel_conf_val(const.DINGTALK, 'image_create_prefix'))
            if img_match_prefix:
                prompt = prompt.split(img_match_prefix, 1)[1].strip()
                context['type'] = 'IMAGE_CREATE'
            id = sender_id
            context['from_user_id'] = str(id)
            reply = super().build_reply_content(prompt, context)
        return reply
         

dd = DingTalkChannel()
handlers = dict()
robots = channel_conf(const.DINGTALK).get('dingtalk_robots')
if robots and len(robots) > 0:
    for robot in robots:
        robot_config = channel_conf(const.DINGTALK).get(robot)
        robot_key = robot_config.get('dingtalk_key')
        group_name = robot_config.get('dingtalk_group')
        handlers[group_name or robot_key] = DingTalkHandler(robot_config)
else:
    handlers['DEFAULT'] = DingTalkHandler(channel_conf(const.DINGTALK))
http_app = Flask(__name__,)


@http_app.route("/", methods=['POST'])
def chat():
    log.info("[DingTalk] chat_headers={}".format(str(request.headers)))
    log.info("[DingTalk] chat={}".format(str(request.data)))
    token = request.headers.get('token')
    data = json.loads(request.data)
    if data:
        content = data['text']['content']
        if not content:
            return
        code = data['robotCode']
        group_name = None
        if 'conversationTitle' in data:
            group_name = data['conversationTitle']
        handler = handlers.get(group_name, handlers.get(code, handlers.get('DEFAULT')))
        if handler.dingtalk_post_token and token != handler.dingtalk_post_token:
            return {'ret': 203}
        handler.chat(dd, data)
        return {'ret': 200}
    
    return {'ret': 201}

