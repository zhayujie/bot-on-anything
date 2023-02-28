import json
import re
from flask import Flask, request, Response
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from common import const
from common.log import logger
from channel.channel import Channel
from config import channel_conf

# 创建 Flask 实例
flask_app = Flask(__name__)

# 创建 Slack Bolt 实例
app = App(token=channel_conf(const.SLACK).get('slack_bot_token'),
          signing_secret=channel_conf(const.SLACK).get('slack_signing_secret'))

# 创建 SlackRequestHandler 实例
handler = SlackRequestHandler(app)


# 监听 Slack app_mention 事件
@app.event("app_mention")
def handle_mention(event, say):
    if 'thread_ts' in event:
        ts = event["thread_ts"]
    else:
        ts = event["ts"]
    reply_text = SlackChannel().handle(event)
    say(text=f"{reply_text}", thread_ts=ts)


# 监听所有来自 Slack 的事件，并将它们转发到 Slack 应用处理
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    data = json.loads(request.data)
    if data['type'] == 'url_verification':
        return f"{data['challenge']}", 200
    handler.handle(request)
    return "ok", 200


class SlackChannel(Channel):
    def startup(self):
        flask_app.run(host='0.0.0.0', port=80)

    def handle(self, event):
        context = dict()
        if 'thread_ts' in event:
            ts = event["thread_ts"]
        else:
            ts = event["ts"]
        context['from_user_id'] = str(ts)
        # 使用正则表达式去除 @xxxx
        plain_text = re.sub(r"<@\w+>", "", event["text"])
        return super().build_reply_content(plain_text, context)
