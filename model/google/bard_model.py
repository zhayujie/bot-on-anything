# encoding:utf-8
from .bard_bot import BardBot
from config import model_conf_val
from model.model import Model
from common import log

user_session = dict()


class BardModel(Model):
    bot: BardBot = None

    def __init__(self):
        try:
            self.cookies = model_conf_val("bard", "cookie")
            self.bot = BardBot(self.cookies)
        except Exception as e:
            log.warn(e)

    def reply(self, query: str, context=None) -> dict[str, str]:
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            bot = user_session.get(context['from_user_id'], None)
            if bot is None:
                bot = self.bot

            user_session[context['from_user_id']] = bot
            log.info(f"[Bard] query={query}")
            answer = bot.ask(query)
            # Bard最多返回3个生成结果,目前暂时选第一个返回
            reply = answer['content']
            if answer['reference']:
                reference = [({'index': item[0], 'reference':item[2][0] if item[2][0] else item[2][1]}) for item in answer['reference'][0]]
                reference.sort(key=lambda x: x['index'], reverse=True)
                reply = self.insert_reference(reply, reference)
            log.warn(f"[Bard] answer={reply}")
            return reply

    async def reply_text_stream(self, query: str, context=None) -> dict:
        reply = self.reply(query, context)
        yield True, reply

    def insert_reference(self, reply: str, reference: list) -> str:
        refer = '\n***\n\n'
        length = len(reference)
        for i, item in enumerate(reference):
            index = item["index"] - 1
            reply = reply[:index] + f'[^{length-i}]' + reply[index:]
            refer += f'- ^{i+1}：{item["reference"]}\n\n'
        refer += '***'
        return reply + refer
