import json
from concurrent.futures import ThreadPoolExecutor
import io
import requests
import telebot
from common.log import logger
from channel.channel import Channel
BOT_TOKEN = '5684663516:AAFRYGIcDalEZzExyoBwt-t33BZjxcTISxg'
bot = telebot.TeleBot(BOT_TOKEN)
thread_pool = ThreadPoolExecutor(max_workers=8)


@bot.message_handler(commands=['ask'])
def send_welcome(msg):
    TelegramChannel().handle(msg)

class TelegramChannel(Channel):
    def __init__(self):
        pass
    def startup(self):
        logger.info("开始启动telegram机器人")
    def handle(self, msg):
        logger.debug("[Telegram]receive msg: " + msg.text)
        thread_pool.submit(self._dosend,msg.text.replace("/ask",""),msg)
    def _dosend(self,query,msg):
        context= dict()
        context['from_user_id'] = '1111'
        reply_text = super().build_reply_content(query, context)
        logger.info('[Telegram]] reply content: {}'.format(reply_text))
        bot.reply_to(msg,reply_text)