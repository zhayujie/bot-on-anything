# encoding:utf-8
import asyncio
from model.model import Model
from config import model_conf_val, common_conf_val
from common import log
from EdgeGPT import Chatbot, ConversationStyle
from ImageGen import ImageGen
from common import functions
import random
import json
# from model.bing.jailbroken_sydney import SydneyBot
user_chathistory = dict()
suggestion_session = dict()

# newBing对话模型逆向网页gitAPI


class BingModel(Model):

    style = 'creative'
    bot: Chatbot = None
    cookies = None


    def __init__(self):
        try:
            self.cookies = model_conf_val("bing", "cookies")
            self.jailbreak = model_conf_val("bing", "jailbreak")
        except Exception as e:
            log.warn(e)

    async def reply_text_stream(self, query: str, context=None):
        pass

    def reply(self, query: str, context=None):
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            return asyncio.run(self.__reply(query, context))
        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query)

    async def __reply(self, query: str, context):
        clear_memory_commands = common_conf_val(
                'clear_memory_commands', ['#清除记忆'])
        if query in clear_memory_commands:
            user_chathistory[context['from_user_id']] = None
            return '记忆已清除'
        
        # deal chat_history
        chat_style = ""
        chat_history = ""
        if user_chathistory.get(context['from_user_id'], None) == None:
            if (self.jailbreak):
                chars = model_conf_val("bing", "jailbreak_prompt")
                chars = chars + "\n\n"
                chat_history = ''.join(chars)
            user_chathistory[context['from_user_id']] = ['creative', chat_history]
        else:
            if not chat_history.endswith("\n\n"):
                if chat_history.endswith("\n"):
                    chat_history += "\n"
                else:
                    chat_history += "\n\n"
        chat_style = user_chathistory[context['from_user_id']][0]
        chat_history = user_chathistory[context['from_user_id']][1]

        query = self.get_quick_ask_query(query, context)
        if query == "输入的序号不在建议列表范围中":
            return "对不起，您输入的序号不在建议列表范围中（数字1-9均会被认为是建议列表），请重新输入。"
        if "[style]已切换至" in query:
            return query

        print(user_chathistory)

        log.info("[NewBing] query={}".format(query))
        bot = await Chatbot.create(cookies=self.cookies)
        reply_text = ""
        reference = ""
        suggestion = ""
        async def stream_output():
            nonlocal chat_history
            nonlocal chat_style
            nonlocal reply_text
            nonlocal reference
            nonlocal suggestion
            chat_history += f"[user](#message)\n{query}\n\n"
            wrote = 0
            async for final, response in bot.ask_stream(
                    prompt=query,
                    raw=True,
                    webpage_context=chat_history,
                    conversation_style=chat_style,
                    search_result=True
            ):
                if not final and response["type"] == 1 and "messages" in response["arguments"][0]:
                    message = response["arguments"][0]["messages"][0]
                    # match message.get("messageType"):
                    if message.get("messageType") == "InternalSearchQuery":
                        pass
                        #chat_history += f"[assistant](#search_query)\n{message['hiddenText']}\n\n"
                    elif message.get("messageType") == "InternalSearchResult":
                        #chat_history += f"[assistant](#search_results)\n{message['hiddenText']}\n\n"
                        reference += f"[assistant](#search_results)\n{message['hiddenText']}"
                    elif message.get("messageType") == None:
                        if "cursor" in response["arguments"][0]:
                            chat_history += "[assistant](#message)\n"
                            wrote = 0
                        if message.get("contentOrigin") == "Apology":
                            log.info("检测到AI生成内容被撤回...已阻止")
                            break
                        else:
                            chat_history += message["text"][wrote:]
                            reply_text += message["text"][wrote:]
                            wrote = len(message["text"])
                            if "suggestedResponses" in message:
                                suggestion = list(map(lambda x: x["text"], message["suggestedResponses"]))
                                chat_history += f"""\n[assistant](#suggestions)
```json
{{"suggestedUserResponses": {suggestion}}}
```\n\n"""
                                break
                if final and not response["item"]["messages"][-1].get("text"):
                    raise Exception("发送的消息被过滤或者对话超时")

        
        try:
            await stream_output()
        except Exception as e:
            log.info(e)

        # 更新历史对话
        user_chathistory[context['from_user_id']][1] = chat_history
        await bot.close()
        return self.build_source_attributions(reply_text, reference, suggestion, context)
        


    def create_img(self, query):
        try:
            log.info("[NewBing] image_query={}".format(query))
            cookie_value = self.cookies[0]["value"]
            image_generator = ImageGen(cookie_value)
            img_list = image_generator.get_images(query)
            log.info("[NewBing] image_list={}".format(img_list))
            return img_list
        except Exception as e:
            log.warn(e)
            return "输入的内容可能违反微软的图片生成内容策略。过多的策略冲突可能会导致你被暂停访问。"

    def get_quick_ask_query(self, query, context):
        if (len(query) == 1 and query.isdigit() and query != "0"):
            suggestion_dict = suggestion_session[context['from_user_id']]
            if (suggestion_dict != None):
                try:
                    query = suggestion_dict[int(query)-1]
                    if (query == None):
                        return "输入的序号不在建议列表范围中"
                    else:
                        query = "在上面的基础上，"+query
                except:
                    return "输入的序号不在建议列表范围中"
        elif(query == "/creative"):
            user_chathistory[context['from_user_id']][0] = query[1:]
            return "[style]已切换至创造模式"
        elif(query == "/balanced"):
            user_chathistory[context['from_user_id']][0] = query[1:]
            return "[style]已切换至平衡模式"
        elif(query == "/precise"):
            user_chathistory[context['from_user_id']][0] = query[1:]
            return "[style]已切换至精确模式"
        return query

    def build_source_attributions(self, reply_text, reference, suggestion, context):
        if not reply_text.endswith("\n\n"):
            if reply_text.endswith("\n"):
                reply_text += "\n"
            else:
                reply_text += "\n\n"

        references = ""
        print(reference[36:-3])
        if 'json' in reference:
            reference_dict = json.loads(reference[36:-3])
            for i in range(len(reference_dict['web_search_results'])):
                r = reference_dict['web_search_results'][i]
                title = r['title']
                url = r['url']
                references += f"{i+1}、[{title}]({url})\n\n"


        suggestions = ""
        suggestion_dict = dict()
        if len(suggestion) > 0:
            for i in range(len(suggestion)):
                suggestion_dict[i] = suggestion[i]
                suggestions += f">{i+1}、{suggestion[i]}\n\n"
            suggestions = "=====\n💡你可能想问(输入序号):\n\n" + suggestions
        suggestion_session[context['from_user_id']] = suggestion_dict

        # throttling = answer["item"]["throttling"]
        # throttling_str = ""

        # if not self.jailbreak:
        #     if throttling["numUserMessagesInConversation"] == throttling["maxNumUserMessagesInConversation"]:
        #         user_session.get(context['from_user_id'], None).reset()
        #         throttling_str = "(对话轮次已达上限，本次聊天已结束，将开启新的对话)"
        #     else:
        #         throttling_str = f"对话轮次: {throttling['numUserMessagesInConversation']}/{throttling['maxNumUserMessagesInConversation']}\n"

        response = f"{reply_text}******\n{references}{suggestions}******\n"
        log.info("[NewBing] reply={}", response)
        return response

