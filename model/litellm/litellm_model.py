# encoding:utf-8

from model.model import Model
from config import model_conf, common_conf_val
from common import const
from common import log
import time

try:
    import litellm
    from litellm.exceptions import (
        AuthenticationError,
        RateLimitError,
        APIConnectionError,
        Timeout,
        NotFoundError,
        BadRequestError,
        ContextWindowExceededError,
    )
except ImportError:
    litellm = None

user_session = dict()


class LiteLLMModel(Model):
    def __init__(self):
        if litellm is None:
            raise ImportError(
                "LiteLLM is required for this model. "
                "Install it with: pip install litellm"
            )
        conf = model_conf(const.LITELLM)
        self.model = conf.get("model", "openai/gpt-4o-mini")
        self.api_key = conf.get("api_key", "")
        self.api_base = conf.get("api_base", "")

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

            if context.get('stream'):
                return self.reply_text_stream(query, new_query, from_user_id)

            reply_content = self.reply_text(new_query, from_user_id, 0)
            return reply_content

    def _build_call_kwargs(self, messages, stream=False):
        conf = model_conf(const.LITELLM)
        call_kwargs = {
            "model": self.model,
            "messages": messages,
            "drop_params": True,
            "stream": stream,
        }
        if conf.get("temperature") is not None:
            call_kwargs["temperature"] = conf.get("temperature", 0.75)
        if conf.get("max_tokens"):
            call_kwargs["max_tokens"] = conf.get("max_tokens")
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.api_base:
            call_kwargs["api_base"] = self.api_base
        return call_kwargs

    def reply_text(self, query, user_id, retry_count=0):
        call_kwargs = self._build_call_kwargs(query)

        try:
            response = litellm.completion(**call_kwargs)
            content = response.choices[0].message.content
            reply_content = content.strip() if content else ""
            used_token = response.usage.total_tokens if response.usage else 0
            log.info("[LITELLM] reply={}", reply_content)
            if reply_content:
                Session.save_session(query, reply_content, user_id, used_token)
            return reply_content
        except RateLimitError as e:
            log.warn(e)
            if retry_count < 3:
                sleep_time = 2 ** retry_count  # 1s, 2s, 4s
                time.sleep(sleep_time)
                log.warn("[LITELLM] RateLimit exceeded, retry #{} in {}s".format(
                    retry_count + 1, sleep_time))
                return self.reply_text(query, user_id, retry_count + 1)
            else:
                return "Rate limit exceeded, please try again later"
        except AuthenticationError as e:
            log.warn(e)
            return "Authentication failed, please check your API key"
        except (APIConnectionError, Timeout) as e:
            log.warn(e)
            log.warn("[LITELLM] Connection failed")
            return "Connection error, please try again later"
        except NotFoundError as e:
            log.warn(e)
            return "Model not found, please check your model configuration"
        except ContextWindowExceededError as e:
            log.warn(e)
            Session.clear_session(user_id)
            return "Context window exceeded, conversation history cleared. Please try again"
        except BadRequestError as e:
            log.warn(e)
            return "Bad request, please check your input"
        except Exception as e:
            log.exception(e)
            Session.clear_session(user_id)
            return "An error occurred, please try again"

    async def reply_text_stream(self, query, context, retry_count=0):
        user_id = context['from_user_id']
        new_query = Session.build_session_query(query, user_id)
        call_kwargs = self._build_call_kwargs(new_query, stream=True)

        try:
            response = litellm.completion(**call_kwargs)
            full_response = ""
            for chunk in response:
                if chunk.choices[0].finish_reason == "stop":
                    break
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    full_response += chunk_content
                yield False, full_response
            Session.save_session(query, full_response, user_id)
            log.info("[LITELLM] reply={}", full_response)
            yield True, full_response
        except RateLimitError as e:
            log.warn(e)
            if retry_count < 3:
                sleep_time = 2 ** retry_count
                time.sleep(sleep_time)
                log.warn("[LITELLM] RateLimit exceeded, retry #{} in {}s".format(
                    retry_count + 1, sleep_time))
                yield True, self.reply_text_stream(query, user_id, retry_count + 1)
            else:
                yield True, "Rate limit exceeded, please try again later"
        except AuthenticationError as e:
            log.warn(e)
            yield True, "Authentication failed, please check your API key"
        except (APIConnectionError, Timeout) as e:
            log.warn(e)
            log.warn("[LITELLM] Connection failed")
            yield True, "Connection error, please try again later"
        except NotFoundError as e:
            log.warn(e)
            yield True, "Model not found, please check your model configuration"
        except ContextWindowExceededError as e:
            log.warn(e)
            Session.clear_session(user_id)
            yield True, "Context window exceeded, conversation history cleared"
        except BadRequestError as e:
            log.warn(e)
            yield True, "Bad request, please check your input"
        except Exception as e:
            log.exception(e)
            Session.clear_session(user_id)
            yield True, "An error occurred, please try again"


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
        if not session:
            return
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
