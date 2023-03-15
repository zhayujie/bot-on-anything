# encoding:utf-8

from model.model import Model
from config import model_conf
from common import const
from common import log
import openai
import time

user_session = dict()

# OpenAI对话模型API (可用)
class ChatGPTModel(Model):
    def __init__(self):
        openai.api_key = model_conf(const.OPEN_AI).get('api_key')
        proxy = model_conf(const.OPEN_AI).get('proxy')
        if proxy:
            openai.proxy = proxy

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            log.info("[CHATGPT] query={}".format(query))
            from_user_id = context['from_user_id']
            if query == '#清除记忆':
                Session.clear_session(from_user_id)
                return '记忆已清除'

            new_query = Session.build_session_query(query, from_user_id)
            log.debug("[CHATGPT] session query={}".format(new_query))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, from_user_id)

            reply_content = self.reply_text(new_query, from_user_id, 0)
            #log.debug("[CHATGPT] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content))
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, query, user_id, retry_count=0):
        try:
            response = openai.ChatCompletion.create(
                model= model_conf(const.OPEN_AI).get("model") or "gpt-3.5-turbo",  # 对话模型的名称
                messages=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            )
            reply_content = response.choices[0]['message']['content']
            used_token = response['usage']['total_tokens']
            log.debug(response)
            log.info("[CHATGPT] reply={}", reply_content)
            if reply_content:
                # save conversation
                Session.save_session(query, reply_content, user_id, used_token)
            return response.choices[0]['message']['content']
        except openai.error.RateLimitError as e:
            # rate limit exception
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[CHATGPT] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(query, user_id, retry_count+1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except openai.error.APIConnectionError as e:
            log.warn(e)
            log.warn("[CHATGPT] APIConnection failed")
            return "我连接不到网络，请稍后重试"
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            return "我没有收到消息，请稍后重试"
        except Exception as e:
            # unknown exception
            log.exception(e)
            Session.clear_session(user_id)
            return "请再问我一次吧"


    def reply_text_stream(self, query, new_query, user_id, retry_count=0):
        try:
            res = openai.Completion.create(
                model="text-davinci-003",  # 对话模型的名称
                prompt=new_query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                #max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["\n\n\n"],
                stream=True
            )
            return self._process_reply_stream(query, res, user_id)

        except openai.error.RateLimitError as e:
            # rate limit exception
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[CHATGPT] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text_stream(query, user_id, retry_count+1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except openai.error.APIConnectionError as e:
            log.warn(e)
            log.warn("[CHATGPT] APIConnection failed")
            return "我连接不到网络，请稍后重试"
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            return "我没有收到消息，请稍后重试"
        except Exception as e:
            # unknown exception
            log.exception(e)
            Session.clear_session(user_id)
            return "请再问我一次吧"


    def _process_reply_stream(
            self,
            query: str,
            reply: dict,
            user_id: str
    ) -> str:
        full_response = ""
        for response in reply:
            if response.get("choices") is None or len(response["choices"]) == 0:
                raise Exception("OpenAI API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("text") is None:
                raise Exception("OpenAI API returned no text")
            if response["choices"][0]["text"] == "<|endoftext|>":
                break
            yield response["choices"][0]["text"]
            full_response += response["choices"][0]["text"]
        if query and full_response:
            Session.save_session(query, full_response, user_id)


    def create_img(self, query, retry_count=0):
        try:
            log.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,    #图片描述
                n=1,             #每次生成图片的数量
                size="256x256"   #图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            log.info("[OPEN_AI] image_url={}".format(image_url))
            return image_url
        except openai.error.RateLimitError as e:
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(query, retry_count+1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            log.exception(e)
            return None


class Session(object):
    @staticmethod
    def build_session_query(query, user_id):
        '''
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query: query content
        :param user_id: from user id
        :return: query content with conversaction
        '''
        session = user_session.get(user_id, [])
        if len(session) == 0:
            system_prompt = model_conf(const.OPEN_AI).get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            user_session[user_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(query, answer, user_id, used_tokens=0):
        max_tokens = model_conf(const.OPEN_AI).get('conversation_max_tokens')
        if not max_tokens or max_tokens > 4000:
            # default value
            max_tokens = 1000
        session = user_session.get(user_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        if used_tokens > max_tokens and len(session) >= 3:
            # pop first conversation (TODO: more accurate calculation)
            session.pop(1)
            session.pop(1)

    @staticmethod
    def clear_session(user_id):
        user_session[user_id] = []

