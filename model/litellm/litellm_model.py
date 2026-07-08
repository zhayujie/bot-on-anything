# encoding:utf-8

from model.model import Model
from config import model_conf, common_conf_val
from common import const
from common import log
import time

user_session = dict()


class LiteLLMModel(Model):
    def __init__(self):
        try:
            import litellm
        except ImportError:
            raise ImportError(
                "LiteLLM is required for this model. "
                "Install it with: pip install litellm"
            )
        conf = model_conf(const.LITELLM)
        self.model = conf.get("model", "gpt-4o-mini")
        self.api_key = conf.get("api_key", "")
        self.api_base = conf.get("api_base", "")

        if self.api_key:
            import os
            os.environ["LITELLM_API_KEY"] = self.api_key
        if self.api_base:
            import os
            os.environ["LITELLM_API_BASE"] = self.api_base

        log.info("[LITELLM] model={} api_base={}".format(self.model, self.api_base))

    def reply(self, query, context=None):
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            log.info("[LITELLM] query={}".format(query))
            from_user_id = context['from_user_id']
            clear_memory_commands = common_conf_val('clear_memory_commands', ['#clear memory'])
            if query in clear_memory_commands:
                Session.clear_session(from_user_id)
                return 'Memory cleared'

            new_query = Session.build_session_query(query, from_user_id)
            log.debug("[LITELLM] session query={}".format(new_query))

            reply_content = self.reply_text(new_query, from_user_id, 0)
            return reply_content

    def reply_text(self, query, user_id, retry_count=0):
        import litellm

        conf = model_conf(const.LITELLM)
        call_kwargs = {
            "model": self.model,
            "messages": query,
            "drop_params": True,
        }
        if conf.get("temperature") is not None:
            call_kwargs["temperature"] = conf.get("temperature", 0.75)
        if conf.get("max_tokens"):
            call_kwargs["max_tokens"] = conf.get("max_tokens")
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.api_base:
            call_kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**call_kwargs)
            reply_content = response.choices[0].message.content
            used_token = response.usage.total_tokens if response.usage else 0
            log.info("[LITELLM] reply={}", reply_content)
            if reply_content:
                Session.save_session(query, reply_content, user_id, used_token)
            return reply_content
        except Exception as e:
            qualname = f"{type(e).__module__}.{type(e).__qualname__}"
            if qualname in {
                "litellm.exceptions.RateLimitError",
            }:
                log.warn(e)
                if retry_count < 1:
                    time.sleep(5)
                    log.warn("[LITELLM] RateLimit exceeded, retry #{}".format(retry_count + 1))
                    return self.reply_text(query, user_id, retry_count + 1)
                else:
                    return "Rate limit exceeded, please try again later"
            elif qualname in {
                "litellm.exceptions.APIConnectionError",
                "litellm.exceptions.Timeout",
            }:
                log.warn(e)
                log.warn("[LITELLM] Connection failed")
                return "Connection error, please try again later"
            else:
                log.exception(e)
                Session.clear_session(user_id)
                return "An error occurred, please try again"


class Session(object):
    @staticmethod
    def build_session_query(query, user_id):
        session = user_session.get(user_id, [])
        if len(session) == 0:
            system_prompt = model_conf(const.LITELLM).get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            user_session[user_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(query, answer, user_id, used_tokens=0):
        max_tokens = model_conf(const.LITELLM).get('conversation_max_tokens')
        max_history_num = model_conf(const.LITELLM).get('max_history_num', None)
        if not max_tokens or max_tokens > 4000:
            max_tokens = 1000
        session = user_session.get(user_id)
        if session:
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        if used_tokens > max_tokens and len(session) >= 3:
            session.pop(1)
            session.pop(1)

        if max_history_num is not None:
            while len(session) > max_history_num * 2 + 1:
                session.pop(1)
                session.pop(1)

    @staticmethod
    def clear_session(user_id):
        user_session[user_id] = []
