# access LinkAI knowledge base platform
# docs: https://link-ai.tech/platform/link-app/wechat

from model.model import Model
from config import model_conf, common_conf_val, channel_conf_val
from common import const
from common import log
import time
import requests
import threading
import os
import re
import json


user_session = dict()

class LinkAIBot(Model):
    # authentication failed
    AUTH_FAILED_CODE = 401
    NO_QUOTA_CODE = 406

    def __init__(self):
        super().__init__()
        # self.sessions = LinkAISessionManager(LinkAISession, model=conf().get("model") or "gpt-3.5-turbo")
        # self.args = {}

    def reply(self, query, context=None):
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            log.info("[LINKAI] query={}".format(query))
            from_user_id = context['from_user_id']
            clear_memory_commands = common_conf_val('clear_memory_commands', ['#清除记忆'])
            if query in clear_memory_commands:
                Session.clear_session(from_user_id)
                return '记忆已清除'
            new_query = Session.build_session_query(query, from_user_id)
            context['session'] = new_query  # 将 new_query 添加到 context 字典中 session
            log.debug("[LINKAI] session query={}".format(new_query))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, context)

            reply_content = self._chat(query, context)
            log.debug("[LINKAI] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content))
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            ok, res = self.create_img(query, 0)
            if ok:
                return [res]
            else:
                return res
        #     return reply
        # else:
        #     # reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
        #     return reply

    def _chat(self, query, context, retry_count=0):
        """
        发起对话请求
        :param query: 请求提示词
        :param context: 对话上下文
        :param retry_count: 当前递归重试次数
        :return: 回复
        """
        if retry_count > 2:
            # exit from retry 2 times
            log.warn("[LINKAI] failed after maximum number of retry times")
            return "请再问我一次吧"

        try:
            linkai_api_key = model_conf(const.LINKAI).get('api_key')
            model = model_conf(const.LINKAI).get("model")  # 对话模型的名称

            app_code = model_conf(const.LINKAI).get("app_code", "")  # LinkAI应用code
            # remove system message
            new_query_session = context.get("session")
            user_id = context['from_user_id']
            if new_query_session[0].get("role") == "system":
                if app_code or model == "wenxin":
                    new_query_session.pop(0)
            body = {
                "app_code": app_code,
                "messages": new_query_session,
                "model": model,     # 对话模型的名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
                "temperature": model_conf(const.LINKAI).get("temperature", 0.75),
                "top_p": model_conf(const.LINKAI).get("top_p", 1),
                "frequency_penalty": model_conf(const.LINKAI).get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": model_conf(const.LINKAI).get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "sender_id": user_id
            }

            log.info(f"[LINKAI] query={query}, app_code={app_code}, model={body.get('model')}")
            headers = {"Authorization": "Bearer " + linkai_api_key}

            # do http request
            base_url = model_conf(const.LINKAI).get("api_base", "https://api.link-ai.tech")
            res = requests.post(url=base_url + "/v1/chat/completions", json=body, headers=headers,
                                timeout=180)
            if res.status_code == 200:
                # execute success
                response = res.json()
                reply_content = response["choices"][0]["message"]["content"]
                total_tokens = response["usage"]["total_tokens"]
                res_code = response.get('code')
                log.info(f"[LINKAI] reply={reply_content}, total_tokens={total_tokens}, res_code={res_code}")
                if res_code == 429:
                    log.warn(f"[LINKAI] 用户访问超出限流配置，sender_id={body.get('sender_id')}")
                else:
                    Session.save_session(query, reply_content, user_id, total_tokens)
                agent_suffix = self._fetch_agent_suffix(response)
                if agent_suffix:
                    reply_content += agent_suffix
                if not agent_suffix:
                    knowledge_suffix = self._fetch_knowledge_search_suffix(response)
                    if knowledge_suffix:
                        reply_content += knowledge_suffix
                # image process
                if response["choices"][0].get("img_urls"):
                    if 'send' in type(context['channel']).__dict__:  # 通道实例所属类的定义是否有send方法
                        thread = threading.Thread(target=self._send_image, args=(context['channel'], context, response["choices"][0].get("img_urls")))
                        thread.start()
                        if response["choices"][0].get("text_content"):
                            reply_content = response["choices"][0].get("text_content")
                    else:
                        reply_content = response["choices"][0].get("text_content", "") + " " + " ".join(response["choices"][0].get("img_urls"))  # 图像生成时候需要合并文本和图片url
                reply_content = self._process_url(reply_content)
                                    
                #    thread = threading.Thread(target=self._send_image, args=(context['channel'], context, response["choices"][0].get("img_urls")))
                #    thread.start()
                #    if response["choices"][0].get("text_content"):
                #        reply_content = response["choices"][0].get("text_content")
                #reply_content = self._process_url(reply_content)
                return reply_content

            else:
                response = res.json()
                error = response.get("error")
                log.error(f"[LINKAI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                if res.status_code >= 500:
                    # server error, need retry
                    time.sleep(2)
                    log.warn(f"[LINKAI] do retry, times={retry_count}")
                    return self._chat(query, context, retry_count + 1)

                error_reply = "提问太快啦，请休息一下再问我吧"
                if res.status_code == 409:
                    error_reply = "这个问题我还没有学会，请问我其它问题吧"
                return error_reply

        except Exception as e:
            log.exception(e)
            # retry
            time.sleep(2)
            log.warn(f"[LINKAI] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)


    # def _process_image_msg(self, app_code: str, session_id: str, query:str, img_cache: dict):
    #     try:
    #         enable_image_input = False
    #         app_info = self._fetch_app_info(app_code)
    #         if not app_info:
    #             log.debug(f"[LinkAI] not found app, can't process images, app_code={app_code}")
    #             return None
    #         plugins = app_info.get("data").get("plugins")
    #         for plugin in plugins:
    #             if plugin.get("input_type") and "IMAGE" in plugin.get("input_type"):
    #                 enable_image_input = True
    #         if not enable_image_input:
    #             return
    #         msg = img_cache.get("msg")
    #         path = img_cache.get("path")
    #         msg.prepare()
    #         log.info(f"[LinkAI] query with images, path={path}")
    #         messages = self._build_vision_msg(query, path)
    #         memory.USER_IMAGE_CACHE[session_id] = None
    #         return messages
    #     except Exception as e:
    #         log.exception(e)
    #
    # def _find_group_mapping_code(self, context):
    #     try:
    #         if context.kwargs.get("isgroup"):
    #             group_name = context.kwargs.get("msg").from_user_nickname
    #             if config.plugin_config and config.plugin_config.get("linkai"):
    #                 linkai_config = config.plugin_config.get("linkai")
    #                 group_mapping = linkai_config.get("group_app_map")
    #                 if group_mapping and group_name:
    #                     return group_mapping.get(group_name)
    #     except Exception as e:
    #         log.exception(e)
    #         return None

    # def _build_vision_msg(self, query: str, path: str):
    #     try:
    #         suffix = utils.get_path_suffix(path)
    #         with open(path, "rb") as file:
    #             base64_str = base64.b64encode(file.read()).decode('utf-8')
    #             messages = [{
    #                 "role": "user",
    #                 "content": [
    #                     {
    #                         "type": "text",
    #                         "text": query
    #                     },
    #                     {
    #                         "type": "image_url",
    #                         "image_url": {
    #                             "url": f"data:image/{suffix};base64,{base64_str}"
    #                         }
    #                     }
    #                 ]
    #             }]
    #             return messages
    #     except Exception as e:
    #         log.exception(e)


    async def reply_text_stream(self, query, context, retry_count=0) :
        if retry_count >= 2:
            # exit from retry 2 times
            log.warn("[LINKAI] failed after maximum number of retry times")
            yield True, "请再问我一次吧"

        try:
            linkai_api_key = model_conf(const.LINKAI).get('api_key')
            model = model_conf(const.LINKAI).get("model")  # 对话模型的名称

            app_code = model_conf(const.LINKAI).get("app_code", "")  # LinkAI应用code
            # remove system message
            new_query_session = context.get("session")
            user_id = context['from_user_id']
            if new_query_session[0].get("role") == "system":
                if app_code or model == "wenxin":
                    new_query_session.pop(0)
            body = {
                "app_code": app_code,
                "messages": new_query_session,
                "model": model,     # 对话模型的名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
                "temperature": model_conf(const.LINKAI).get("temperature", 0.75),
                "top_p": model_conf(const.LINKAI).get("top_p", 1),
                "frequency_penalty": model_conf(const.LINKAI).get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": model_conf(const.LINKAI).get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "sender_id": user_id,
                "stream": True
            }
            if self.args.get("max_tokens"):
                body["max_tokens"] = self.args.get("max_tokens")
            headers = {"Authorization": "Bearer " + linkai_api_key}

            # do http request
            base_url = model_conf(const.LINKAI).get("api_base", "https://api.link-ai.tech")
            res = requests.post(url=base_url + "/v1/chat/completions", json=body, headers=headers, stream=True,
                                timeout=180)
            if res.status_code == 200:
                full_response = ""
                for i in res.iter_lines():
                    st = str(i, encoding="utf-8")
                    st = st.replace("data: ", "", 1)
                    if st:
                        if st == "[DONE]":  # 输出结束
                            break
                        chunk = json.loads(st)
                        if not chunk.get("choices"):
                            continue
                        chunk_message = chunk["choices"][0]["delta"].get("content")
                        if (chunk_message):
                            full_response += chunk_message
                        yield False, full_response
                Session.save_session(query, full_response, user_id)
                log.info("[LinkAI]: reply={}", full_response)
                yield True, full_response
            else:
                response = res.json()
                error = response.get("error")
                log.error(f"[LINKAI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                if res.status_code >= 500:
                    # server error, need retry
                    time.sleep(2)
                    log.warn(f"[LINKAI] do retry, times={retry_count}")
                    yield True, self.reply_text_stream(query, context, retry_count+1)
                error_reply = "提问太快啦，请休息一下再问我吧"
                if res.status_code == 409:
                    error_reply = "这个问题我还没有学会，请问我其它问题吧"
                yield True, error_reply
        except Exception as e:
            log.exception(e)
            # retry
            time.sleep(2)
            log.warn(f"[LINKAI] do retry, times={retry_count}")
            yield True, self.reply_text_stream(query, context, retry_count+1)

    # def _fetch_app_info(self, app_code: str):
    #     headers = {"Authorization": "Bearer " + conf().get("linkai_api_key")}
    #     # do http request
    #     base_url = conf().get("linkai_api_base", "https://api.link-ai.chat")
    #     params = {"app_code": app_code}
    #     res = requests.get(url=base_url + "/v1/app/info", params=params, headers=headers, timeout=(5, 10))
    #     if res.status_code == 200:
    #         return res.json()
    #     else:
    #         log.warning(f"[LinkAI] find app info exception, res={res}")

    def create_img(self, query, retry_count=0, api_key=None):
        try:
            log.info("[LinkImage] image_query={}".format(query))
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {model_conf(const.LINKAI).get('api_key')}"
            }
            data = {
                "prompt": query,
                "n": 1,
                "model": model_conf(const.LINKAI).get("text_to_image") or "dall-e-3",
                "response_format": "url",
            }
            url = model_conf(const.LINKAI).get("linkai_api_base", "https://api.link-ai.tech") + "/v1/images/generations"
            res = requests.post(url, headers=headers, json=data, timeout=(5, 90))
            t2 = time.time()
            image_url = res.json()["data"][0]["url"]
            log.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url

        except Exception as e:
            log.error(format(e))
            return False, "画图出现问题，请休息一下再问我吧"


    def _fetch_knowledge_search_suffix(self, response) -> str:
        try:
            if response.get("knowledge_base"):
                search_hit = response.get("knowledge_base").get("search_hit")
                first_similarity = response.get("knowledge_base").get("first_similarity")
                log.info(f"[LINKAI] knowledge base, search_hit={search_hit}, first_similarity={first_similarity}")
                # plugin_config = pconf("linkai")
                # if plugin_config and plugin_config.get("knowledge_base") and plugin_config.get("knowledge_base").get("search_miss_text_enabled"):
                #     search_miss_similarity = plugin_config.get("knowledge_base").get("search_miss_similarity")
                #     search_miss_text = plugin_config.get("knowledge_base").get("search_miss_suffix")
                #     if not search_hit:
                #         return search_miss_text
                #     if search_miss_similarity and float(search_miss_similarity) > first_similarity:
                #         return search_miss_text
        except Exception as e:
            log.exception(e)


    def _fetch_agent_suffix(self, response):
        try:
            plugin_list = []
            log.debug(f"[LinkAgent] res={response}")
            if response.get("agent") and response.get("agent").get("chain") and response.get("agent").get("need_show_plugin"):
                chain = response.get("agent").get("chain")
                suffix = "\n\n- - - - - - - - - - - -"
                i = 0
                for turn in chain:
                    plugin_name = turn.get('plugin_name')
                    suffix += "\n"
                    need_show_thought = response.get("agent").get("need_show_thought")
                    if turn.get("thought") and plugin_name and need_show_thought:
                        suffix += f"{turn.get('thought')}\n"
                    if plugin_name:
                        plugin_list.append(turn.get('plugin_name'))
                        if turn.get('plugin_icon'):
                            suffix += f"{turn.get('plugin_icon')} "
                        suffix += f"{turn.get('plugin_name')}"
                        if turn.get('plugin_input'):
                            suffix += f"：{turn.get('plugin_input')}"
                    if i < len(chain) - 1:
                        suffix += "\n"
                    i += 1
                log.info(f"[LinkAgent] use plugins: {plugin_list}")
                return suffix
        except Exception as e:
            log.exception(e)

    # 将markdown格式的链接转为普通的链接
    def _process_url(self, text):
        try:
            url_pattern = re.compile(r'\[(.*?)\]\((http[s]?://.*?)\)')
            def replace_markdown_url(match):
                return f"{match.group(2)}"
            return url_pattern.sub(replace_markdown_url, text)
        except Exception as e:
            log.error(e)

    def _send_image(self, channel, context, image_urls):
        if not image_urls:
            return
        max_send_num = model_conf(const.LINKAI).get("max_media_send_count")
        send_interval = model_conf(const.LINKAI).get("media_send_interval")
        try:
            i = 0
            for url in image_urls:
                if max_send_num and i >= max_send_num:
                    continue
                i += 1
                # if url.endswith(".mp4"):
                #     reply_type = ReplyType.VIDEO_URL
                # elif url.endswith(".pdf") or url.endswith(".doc") or url.endswith(".docx") or url.endswith(".csv"):
                #     reply_type = ReplyType.FILE
                #     url = _download_file(url)
                #     if not url:
                #         continue
                # else:
                #     reply_type = ReplyType.IMAGE_URL
                reply = url
                channel.send(reply, context["from_user_id"])
                if send_interval:
                    time.sleep(send_interval)
        except Exception as e:
            log.error(e)


def _download_file(url: str):
    try:
        file_path = "tmp"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = url.split("/")[-1]  # 获取文件名
        file_path = os.path.join(file_path, file_name)
        response = requests.get(url)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        log.warn(e)

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
            system_prompt = model_conf(const.LINKAI).get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            user_session[user_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(query, answer, user_id, used_tokens=0):
        max_tokens = model_conf(const.LINKAI).get('conversation_max_tokens')
        max_history_num = model_conf(const.LINKAI).get('max_history_num', None)
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

        if max_history_num is not None:
            while len(session) > max_history_num * 2 + 1:
                session.pop(1)
                session.pop(1)

    @staticmethod
    def clear_session(user_id):
        user_session[user_id] = []

#
# class LinkAISessionManager(SessionManager):
#     def session_msg_query(self, query, session_id):
#         session = self.build_session(session_id)
#         messages = session.messages + [{"role": "user", "content": query}]
#         return messages
#
#     def session_reply(self, reply, session_id, total_tokens=None, query=None):
#         session = self.build_session(session_id)
#         if query:
#             session.add_query(query)
#         session.add_reply(reply)
#         try:
#             max_tokens = conf().get("conversation_max_tokens", 2500)
#             tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
#             log.debug(f"[LinkAI] chat history, before tokens={total_tokens}, now tokens={tokens_cnt}")
#         except Exception as e:
#             log.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
#         return session
#
#
# class LinkAISession(ChatGPTSession):
#     def calc_tokens(self):
#         if not self.messages:
#             return 0
#         return len(str(self.messages))
#
#     def discard_exceeding(self, max_tokens, cur_tokens=None):
#         cur_tokens = self.calc_tokens()
#         if cur_tokens > max_tokens:
#             for i in range(0, len(self.messages)):
#                 if i > 0 and self.messages[i].get("role") == "assistant" and self.messages[i - 1].get("role") == "user":
#                     self.messages.pop(i)
#                     self.messages.pop(i - 1)
#                     return self.calc_tokens()
#         return cur_tokens
