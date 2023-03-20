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

@bot.on_message('group')
def handle_private_msg(event: Event):
    log.info("event: {}", event)
    QQChannel().handle_group(event)

class QQChannel(Channel):
    def startup(self):
        bot.run(host='127.0.0.1', port=8080)

    # private chat
    def handle(self, msg):
        thread_pool.submit(self._do_handle, msg)

    def _do_handle(self, msg):
        context = dict()
        log.info("event: {}", "do_handle")
        context['from_user_id'] = msg.user_id
        reply_text = super().build_reply_content(msg.message, context)
        bot.sync.send_private_msg(user_id=msg.user_id, message=reply_text)

    # group chat
    def handle_group(self, msg):
        thread_pool.submit(self._do_handle_group, msg)

    def _do_handle_group(self, msg):
        context = dict()
        if msg.message and msg.message.find('CQ:at'):
            receiver = msg.message.split('qq=')[1].split(']')[0]
            if receiver == str(msg['self_id']):
                text_list = msg.message.split(']', 2)
                if len(text_list) == 2 and len(text_list[1]) > 0:
                    query = text_list[1].strip()
                    context['from_user_id'] = str(msg.user_id)
                    reply_text = super().build_reply_content(query, context)
                    reply_text = '[CQ:at,qq=' + str(msg.user_id) + '] ' + reply_text

                    bot.sync.send_group_msg(group_id=msg['group_id'], message=reply_text)
