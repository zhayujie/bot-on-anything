import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from common import const
from common.log import logger
from channel.channel import Channel
from config import channel_conf

# 创建 Slack Bolt 实例
app = App(token=channel_conf(const.SLACK).get('slack_bot_token'))

# 创建 SocketModeHandler 实例
handler = SocketModeHandler(app=app,
                            app_token=channel_conf(const.SLACK).get('slack_app_token'))

# 监听 Slack app_mention 事件
@app.event("app_mention")
def handle_mention(event, say):
    if 'thread_ts' in event:
        ts = event["thread_ts"]
    else:
        ts = event["ts"]
    reply_text = SlackChannel().handle(event)
    say(text=f"{reply_text}", thread_ts=ts)

class SlackChannel(Channel):
    def startup(self):
        handler.start()

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
