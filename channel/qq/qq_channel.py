from channel.channel import Channel
from aiocqhttp import CQHttp, Event
from common import log
from concurrent.futures import ThreadPoolExecutor

bot = CQHttp(api_root='http://127.0.0.1:5700')
thread_pool = ThreadPoolExecutor(max_workers=8)

@bot.on_message('private')
def handle_private_msg(event: Event):
    log.info("event: {}", event)
    QQChannel().handle(event)

class QQChannel(Channel):
    def startup(self):
        bot.run(host='127.0.0.1', port=8080)

    def handle(self, msg):
        thread_pool.submit(self._do_handle, msg)

    def _do_handle(self, msg):
        context = dict()
        log.info("event: {}", "do_handle")
        context['from_user_id'] = msg.user_id
        reply_text = super().build_reply_content(msg.message, context)
        bot.sync.send_private_msg(user_id=msg.user_id, message=reply_text)
