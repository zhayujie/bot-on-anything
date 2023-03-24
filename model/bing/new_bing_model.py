# encoding:utf-8
import asyncio
from model.model import Model
from config import model_conf_val
from common import log
from EdgeGPT import Chatbot, ConversationStyle
from ImageGen import ImageGen
user_session = dict()
suggestion_session = dict()
# newBing对话模型逆向网页gitAPI


class BingModel(Model):

    style = ConversationStyle.creative
    bot: Chatbot = None
    cookies: list = None

    def __init__(self):
        try:
            self.cookies = model_conf_val("bing", "cookies")
            self.bot = Chatbot(cookies=self.cookies)
        except Exception as e:
            log.exception(e)

    def reply(self, query: str, context=None) -> tuple[str, dict]:
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            bot = user_session.get(context['from_user_id'], None)
            if (bot == None):
                bot = self.bot
            else:
                if (len(query) == 1 and query.isdigit() and query != "0"):
                    suggestion_dict = suggestion_session[context['from_user_id']]
                    if (suggestion_dict != None):
                        query = suggestion_dict[int(query)-1]
                        if (query == None):
                            return "输入的序号不在建议列表范围中"
                        else:
                            query = "在上面的基础上，"+query
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

                suggestion = ""
                if "suggestedResponses" in reply:
                    suggestion_dict = dict()
                    for i, attribution in enumerate(reply["suggestedResponses"]):
                        suggestion_dict[i] = attribution["text"]
                        suggestion += f">{i+1}、{attribution['text']}\n\n"
                    suggestion_session[context['from_user_id']
                                       ] = suggestion_dict

                if len(suggestion) > 0:
                    suggestion = "***\n你可以通过输入序号快速追问我以下建议问题：\n\n"+suggestion

                throttling = answer["item"]["throttling"]
                throttling_str = ""

                if throttling["numUserMessagesInConversation"] == throttling["maxNumUserMessagesInConversation"]:
                    self.reset_chat(context['from_user_id'])
                    throttling_str = "(对话轮次已达上限，本次聊天已结束，将开启新的对话)"
                else:
                    throttling_str = f"对话轮次: {throttling['numUserMessagesInConversation']}/{throttling['maxNumUserMessagesInConversation']}\n"

                response = f"{reply_text}\n{reference}\n{suggestion}\n***\n{throttling_str}"
                log.info("[NewBing] reply={}", response)
                user_session[context['from_user_id']] = bot
                return response
            else:
                self.reset_chat(context['from_user_id'])
                log.warn("[NewBing] reply={}", answer)
                return "对话被接口拒绝，已开启新的一轮对话。"
        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query)

    def create_img(self, query):
        try:
            log.info("[NewBing] image_query={}".format(query))
            cookie_value=self.cookies[0]["value"]
            image_generator = ImageGen(cookie_value)
            img_list = image_generator.get_images(query)
            log.info("[NewBing] image_list={}".format(img_list))
            return img_list[0]
        except Exception as e:
            log.exception(e)
            return None

    def reset_chat(self, from_user_id):
        asyncio.run(user_session.get(from_user_id, None).reset())
