from concurrent.futures import ThreadPoolExecutor
import io
import requests
import telebot
from common import const
from common.log import logger
from channel.channel import Channel
from config import channel_conf_val, channel_conf
bot = telebot.TeleBot(token=channel_conf(const.TELEGRAM).get('bot_token'))
thread_pool = ThreadPoolExecutor(max_workers=8)

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "<a>我是chatGPT机器人，开始和我聊天吧!</a>", parse_mode = "HTML")

# 处理文本类型消息
@bot.message_handler(content_types=['text'])
def send_welcome(msg):
    # telegram消息处理
    TelegramChannel().handle(msg)

class TelegramChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        logger.info("开始启动[telegram]机器人")
        bot.infinity_polling()

    def handle(self, msg):
        logger.debug("[Telegram] receive msg: " + msg.text)
        img_match_prefix = self.check_prefix(msg, channel_conf_val(const.TELEGRAM, 'image_create_prefix'))
        # 如果是图片请求
        if img_match_prefix:
            thread_pool.submit(self._do_send_img, msg, str(msg.chat.id))
        else:
            thread_pool.submit(self._dosend,msg.text,msg)
        
    def _dosend(self,query,msg):
        context= dict()
        context['from_user_id'] = str(msg.chat.id)
        reply_text = super().build_reply_content(query, context)
        logger.info('[Telegram] reply content: {}'.format(reply_text))
        bot.reply_to(msg,reply_text)
        
    def _do_send_img(self, msg, reply_user_id):
        try:
            if not msg:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_urls = super().build_reply_content(msg.text, context)
            if not img_urls:
                return
            if not isinstance(img_urls, list):
                bot.reply_to(msg,img_urls)
                return
            for url in img_urls:
            # 图片下载
                pic_res = requests.get(url, stream=True)
                image_storage = io.BytesIO()
                for block in pic_res.iter_content(1024):
                    image_storage.write(block)
                image_storage.seek(0)

                # 图片发送
                logger.info('[Telegrame] sendImage, receiver={}'.format(reply_user_id))
                bot.send_photo(msg.chat.id,image_storage)
        except Exception as e:
            logger.exception(e)

    def check_prefix(self, msg, prefix_list):
        if not prefix_list:
            return None
        for prefix in prefix_list:
            if msg.text.startswith(prefix):
                return prefix
        return None
