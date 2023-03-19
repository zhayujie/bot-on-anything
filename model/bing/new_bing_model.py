# encoding:utf-8
import asyncio
from model.model import Model
from config import model_conf_val
from common import log
from EdgeGPT import Chatbot, ConversationStyle

user_session = dict()
# newBing对话模型逆向网页gitAPI

class BingModel(Model):

    style = ConversationStyle.creative
    bot: Chatbot = None

    def __init__(self):
        try:
            self.bot = Chatbot(cookies=model_conf_val("bing", "cookies"))
        except Exception as e:
            log.exception(e)

    def reply(self, query: str, context=None) -> tuple[str, dict]:
        bot = user_session.get(context['from_user_id'], None)
        if (bot == None):
            bot = self.bot
        log.info("[NewBing] query={}".format(query))
        task = bot.ask(query, conversation_style=self.style)
        answer = asyncio.run(task)

        # 最新一条回复
        reply = answer["item"]["messages"][-1]
        reply_text = reply["text"]
        reference = ""
        if "sourceAttributions" in reply:
            for i, attribution in enumerate(reply["sourceAttributions"]):
                display_name = attribution["providerDisplayName"]
                url = attribution["seeMoreUrl"]
                reference += f"{i+1}、[{display_name}]({url})\n\n"

            if len(reference) > 0:
                reference = "***\n"+reference
            throttling = answer["item"]["throttling"]
            throttling_str = ""

            if throttling["numUserMessagesInConversation"] == throttling["maxNumUserMessagesInConversation"]:
                self.reset_chat(context['from_user_id'])
                throttling_str = "(对话轮次已达上限，本次聊天已结束，将开启新的对话)"
            else:
                throttling_str = f"对话轮次: {throttling['numUserMessagesInConversation']}/{throttling['maxNumUserMessagesInConversation']}\n"

            response = f"{reply_text}\n{reference}\n***\n{throttling_str}"
            log.info("[NewBing] reply={}", response)
            user_session[context['from_user_id']] = bot
            return response
        else:
            self.reset_chat(context['from_user_id'])
            log.warn("[NewBing] reply={}", answer)
            return "对话被接口拒绝，已开启新的一轮对话。"

    def reset_chat(self, from_user_id):
        asyncio.run(user_session.get(from_user_id, None).reset())
