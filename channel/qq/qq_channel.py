from channel.channel import Channel
from aiocqhttp import CQHttp, Event
from common import log
import requests
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
        if msg.message.startswith("#绘画："):
                context['type'] = 'IMAGE_CREATE'
                msg.message = msg.message.replace("#绘画：","",1)
        reply_text = super().build_reply_content(msg.message, context)
        if context.get('type', None) == 'IMAGE_CREATE' and reply_text != "输入的内容可能违反微软的图片生成内容策略。过多的策略冲突可能会导致你被暂停访问。":
            bot.sync.send_private_msg(user_id=msg.user_id, message="已为您生成"+msg.message)
            for reply in reply_text:
                send_private_message_image(uid=msg.user_id, pic_url=reply, msg='')
        else:
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
                    if query.startswith("#绘画："):
                        context['type'] = 'IMAGE_CREATE'
                        query = query.replace("#绘画：","",1)
                    reply_text = super().build_reply_content(query, context)

                    if context.get('type', None) == 'IMAGE_CREATE':
                       if any("http" in reply for reply in reply_text):
                          bot.sync.send_group_msg(group_id=msg['group_id'], message=
                                                '[CQ:at,qq=' + str(msg.user_id) + '] 已经为您生成图片')
                          for reply in reply_text:
                              send_group_message_image(gid=msg['group_id'], pic_url=reply, uid=str(msg.user_id), msg='')
                       else:
                          bot.sync.send_group_msg(group_id=msg['group_id'], message='[CQ:at,qq=' + str(msg.user_id) + '] 已屏蔽')
                    else:
                        reply_text = '[CQ:at,qq=' + str(msg.user_id) + '] ' + reply_text
                        bot.sync.send_group_msg(group_id=msg['group_id'], message=reply_text)

def send_private_message_image(uid, pic_url, msg):
    try:
        message = "[CQ:image,file=" + pic_url + "]"
        if msg != "":
            message = msg + '\n' + message
        res = requests.post(url="http://localhost:5700/send_private_msg",
                            params={'user_id': int(uid), 'message': message}).json()
        if res["status"] == "ok":
            print("图片发送成功")
        else:
            print(res)
            print("图片发送失败，错误信息：" + str(res['wording']))

    except Exception as error:
        print("图片发送失败")
        print(error)

def send_group_message_image(gid, pic_url, uid, msg):
    try:
        message = "[CQ:image,file=" + pic_url + "]"
        if msg != "":
            message = msg + '\n' + message
        message = str('[CQ:at,qq=%s]\n' % uid) + message  # @发言人
        res = requests.post(url="http://localhost:5700/send_group_msg",
                            params={'group_id': int(gid), 'message': message}).json()
        if res["status"] == "ok":
            print("群图片发送成功")
        else:
            print("群图片发送失败，错误信息：" + str(res['wording']))
    except Exception as error:
        print("群图片发送失败")
        print(error)
