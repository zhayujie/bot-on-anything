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

class DDChannel(Channel):
    def __init__(self):
        self.dd_token = channel_conf(const.DINGDING).get('dd_token')
        self.dd_post_token = channel_conf(const.DINGDING).get('dd_post_token')
        self.dd_secret = channel_conf(const.DINGDING).get('dd_secret')
        log.info("[DingDing] dd_secret={}, dd_token={} dd_post_token={}".format(self.dd_secret, self.dd_token, self.dd_post_token))

    def startup(self):
        
        http_app.run(host='0.0.0.0', port=channel_conf(const.DINGDING).get('port'))
        
    def notify_dingding(self, answer):
        data = {
            "msgtype": "text",
            "text": {
                "content": answer
            },

            "at": {
                "atMobiles": [
                    ""
                ],
                "isAtAll": False
            }
        }

        timestamp = round(time.time() * 1000)
        secret_enc = bytes(self.dd_secret, encoding='utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.dd_secret)
        string_to_sign_enc = bytes(string_to_sign, encoding='utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc,
                             digestmod=hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(hmac_code))

        notify_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dd_token}&timestamp={timestamp}&sign={sign}"
        try:
            r = requests.post(notify_url, json=data)
            reply = r.json()
            # log.info("[DingDing] reply={}".format(str(reply)))
        except Exception as e:
            log.error(e)

    def handle(self, data):
        prompt = data['text']['content']
        conversation_id = data['conversationId']
        sender_id = data['senderId']
        context = dict()
        img_match_prefix = functions.check_prefix(
            prompt, channel_conf_val(const.DINGDING, 'image_create_prefix'))
        if img_match_prefix:
            prompt = prompt.split(img_match_prefix, 1)[1].strip()
            context['type'] = 'IMAGE_CREATE'
        id = sender_id
        context['from_user_id'] = str(id)
        reply = super().build_reply_content(prompt, context)
        if img_match_prefix:
            if not isinstance(reply, list):
                return reply
            images = ""
            for url in reply:
                images += f"[!['IMAGE_CREATE']({url})]({url})\n"
            reply = images
        return reply


dd = DDChannel()
http_app = Flask(__name__,)


@http_app.route("/", methods=['POST'])
def chat():
    # log.info("[DingDing] chat_headers={}".format(str(request.headers)))
    log.info("[DingDing] chat={}".format(str(request.data)))
    token = request.headers.get('token')
    if dd.dd_post_token and token != dd.dd_post_token:
        return {'ret': 203}
    #TODO: Verify identity
    data = json.loads(request.data)
    if data:
        content = data['text']['content']
        if not content:
            return
        reply_text = dd.handle(data=data)
        dd.notify_dingding(reply_text)
        return {'ret': 200}
    return {'ret': 201}
