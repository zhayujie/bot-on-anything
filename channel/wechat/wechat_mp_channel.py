import werobot
import time
from config import channel_conf
from common import const
from common.log import logger
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor

robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)
cache = {}

@robot.text
def hello_world(msg):
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
        robot.run()

    def handle(self, msg, count=0):
        context = dict()
        context['from_user_id'] = msg.source
        key = msg.content + '|' + msg.source
        res = cache.get(key)
        if not res:
            thread_pool.submit(self._do_send, msg.content, context)
            temp = {'flag': True, 'req_times': 1}
            cache[key] = temp
            if count < 10:
                time.sleep(2)
                return self.handle(msg, count+1)

        elif res.get('flag', False) and res.get('data', None):
            cache.pop(key)
            return res['data']

        elif res.get('flag', False) and not res.get('data', None):
            if res.get('req_times') == 3 and count == 8:
                return '不好意思我的CPU烧了，请再问我一次吧~'
            if count < 10:
                time.sleep(0.5)
                return self.handle(msg, count+1)
        return "请再说一次"


    def _do_send(self, query, context):
        reply_text = super().build_reply_content(query, context)
        logger.info('[WX_Public] reply content: {}'.format(reply_text))
        key = query + '|' + context['from_user_id']
        cache[key] = {'flag': True, 'data': reply_text}
