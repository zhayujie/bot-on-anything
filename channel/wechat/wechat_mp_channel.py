import werobot
import time
from config import channel_conf
from common import const
from common.log import logger
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
import os



robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)
cache = {}

@robot.text
def hello_world(msg):
    with open('sensitive_words.txt', 'r', encoding='utf-8') as f: #加入检测违规词
        sensitive_wordss = [msg.content[i:i+2] for i in range(0, len(msg.content), 2)]
        found = False
        #判断文件是否为空
        if not os.path.getsize('sensitive_words.txt'):
            found = False
        else:
            for i in sensitive_wordss:
                if i in f.read():
                    found = True
                    break
                else:
                    found = False
        if found:
            return '你输入的内容包含敏感词汇'
        else:
            logger.info('[WX_Public] receive public msg: {}, userId: {}'.format(msg.content, msg.source))
            key = msg.content + '|' + msg.source
            if cache.get(key):
                # request time
                cache.get(key)['req_times'] += 1
            return WechatSubsribeAccount().handle(msg)


class WechatSubsribeAccount(Channel):
    def startup(self):
        logger.info('[WX_Public] Wechat Public account service start!')
        robot.config['PORT'] = channel_conf(const.WECHAT_MP).get('port')
        robot.config['HOST'] = '0.0.0.0'
        robot.run()

    def handle(self, msg, count=0):
        context = dict()
        context['from_user_id'] = msg.source
        key = msg.source
        res = cache.get(key)
        if msg.content == "继续":
            if not res or res.get("status") == "done":
                return "目前不在等待回复状态，请输入对话"
            if res.get("status") == "waiting":
                return "还在处理中，请稍后再试"
            elif res.get("status") == "success":
                cache[key] = {"status":"done"}
                return res.get("data")
            else:
                return "目前不在等待回复状态，请输入对话"
        elif not res or res.get('status') == "done":
            thread_pool.submit(self._do_send, msg.content, context)
            return "已开始处理，请稍等片刻后输入\"继续\"查看回复"
        else:
            if res.get('status') == "done":
                reply = res.get("data")
                thread_pool.submit(self._do_send, msg.content, context)
                return reply
            else:
                return "上一句对话正在处理中，请稍后输入\"继续\"查看回复"

    def _do_send(self, query, context):
        key = context['from_user_id']
        cache[key] = {"status": "waiting"}
        reply_text = super().build_reply_content(query, context)
        logger.info('[WX_Public] reply content: {}'.format(reply_text))

        cache[key] = {"status": "success", "data": reply_text}
