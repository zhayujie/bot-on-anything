# encoding:utf-8
import asyncio
import time
import websockets
import random
import uuid
import EdgeGPT
from EdgeGPT import ChatHubRequest, Chatbot, Conversation, ChatHub
from typing import Generator
from config import model_conf_val


class SydneyBot(Chatbot):
    def __init__(
        self,
        cookiePath: str = "",
        cookies: dict | None = None,
        proxy: str | None = None,
        options: dict | None = None,
    ) -> None:
        self.conversations_cache = {}
        self.parent_message_id = 0
        self.user_message_id = 0
        self.conversation_key = uuid.uuid4()
        self.cookiePath: str = cookiePath
        self.cookies: dict | None = cookies
        self.proxy: str | None = proxy
        self.chat_hub: SydneyHub
        cache_options = options.get('cache', {})
        cache_options['namespace'] = cache_options.get('namespace', 'bing')
        self.conversations_cache = cache_options

    @staticmethod
    def get_messages_for_conversation(messages, parent_message_id):
        ordered_messages = []
        current_message_id = parent_message_id
        while current_message_id:
            message = next(
                (m for m in messages if m['id'] == current_message_id), None)
            if not message:
                break
            ordered_messages.insert(0, message)
            current_message_id = message.get('parentMessageId')
        return ordered_messages

    async def ask_stream(
        self,
        prompt: str,
        conversation_style: EdgeGPT.CONVERSATION_STYLE_TYPE = None,
        message_id: str = None
    ) -> dict:
        # 开启新对话
        self.chat_hub = SydneyHub(Conversation(
            self.cookiePath, self.cookies, self.proxy))
        self.parent_message_id = message_id if message_id != None else uuid.uuid4()
        # 构造历史对话字符串,更新SydneyHubRequest的历史对话
        conversation = self.conversations_cache.get(self.conversation_key)
        if conversation is None:
            conversation = {
                "messages": [],
                "createdAt": int(time.time()*1000)
            }
        previous_cached_messages = ""
        for conversation_message in self.get_messages_for_conversation(conversation["messages"], self.parent_message_id):
            previous_cached_messages += f"{conversation_message['role'].replace('bot', 'AI')}:\n{conversation_message['message']}\n\n"
        chars = list(model_conf_val("bing", "jailbreak_prompt"))
        chars = [('-' + c if random.random() < 0.5 else '_' + c)
                 if i > 0 else c for i, c in enumerate(chars)]
        previous_messages = ''.join(chars)
        self.chat_hub.request.previous_messages = previous_messages + \
            "\n\n"+previous_cached_messages

        # 将当前提问加入历史对话列表
        self.user_message_id = uuid.uuid4()
        user_message = {
            "id": self.user_message_id,
            "parentMessageId": self.parent_message_id,
            "role": 'User',
            "message": prompt,
        }
        conversation["messages"].append(user_message)
        self.conversations_cache[self.conversation_key] = conversation

        async for final, response in self.chat_hub.ask_stream(
            prompt=prompt,
            conversation_style=conversation_style
        ):
            if final:
                try:
                    if self.chat_hub.wss and not self.chat_hub.wss.closed:
                        await self.chat_hub.wss.close()
                    self.update_reply_cache(response["item"]["messages"][-1])
                except Exception as e:
                    self.conversations_cache[self.conversation_key]["messages"].pop()
                    yield True, f"AI生成内容被微软内容过滤器拦截,已删除最后一次提问的记忆,请尝试使用其他文字描述问题,若AI依然无法正常回复,请清除全部记忆后再次尝试"
            yield final, response

    async def ask(
        self,
        prompt: str,
        conversation_style: EdgeGPT.CONVERSATION_STYLE_TYPE = None,
        message_id: str = None
    ) -> dict:
        async for final, response in self.ask_stream(
            prompt=prompt,
            conversation_style=conversation_style,
            message_id=message_id
        ):
            if final:
                self.update_reply_cache(response["item"]["messages"][-1])
                return response

    def update_reply_cache(
        self,
        reply,
    ) -> None:
        # 将回复加入历史对话列表
        replyMessage = {
            "id": uuid.uuid4(),
            "parentMessageId": self.user_message_id,
            "role": 'Bing',
            "message": reply["text"],
            "details": reply,
        }
        self.conversations_cache[self.conversation_key]["messages"].append(
            replyMessage)
        self.user_message_id = replyMessage["id"]


class SydneyHub(ChatHub):
    """
    Chat API
    """

    def __init__(self, conversation: Conversation) -> None:
        self.wss: websockets.WebSocketClientProtocol | None = None
        self.request: SydneyHubRequest
        self.loop: bool
        self.task: asyncio.Task
        self.request = SydneyHubRequest(
            conversation_signature=conversation.struct["conversationSignature"],
            client_id=conversation.struct["clientId"],
            conversation_id=conversation.struct["conversationId"],
        )

    async def ask_stream(
        self,
        prompt: str,
        wss_link: str = "wss://sydney.bing.com/sydney/ChatHub",
        conversation_style: EdgeGPT.CONVERSATION_STYLE_TYPE = None,
    ) -> Generator[str, None, None]:
        async for item in super().ask_stream(prompt=prompt, conversation_style=conversation_style, wss_link=wss_link):
            yield item


class SydneyHubRequest(ChatHubRequest):

    def __init__(
        self,
        conversation_signature: str,
        client_id: str,
        conversation_id: str,
        invocation_id: int = 0,
    ) -> None:
        super().__init__(conversation_signature=conversation_signature, client_id=client_id,
                         conversation_id=conversation_id, invocation_id=invocation_id)
        self.previous_messages = ""

    def update(
        self,
        prompt: str,
        conversation_style: EdgeGPT.CONVERSATION_STYLE_TYPE,
        options: list | None = None,
    ) -> None:
        self.invocation_id = 0
        super().update(prompt=prompt, conversation_style=conversation_style, options=options)
        self.struct["arguments"][0]["message"]["messageType"] = "SearchQuery"
        self.struct["arguments"][0]["previousMessages"] = [
            {"text":  "N/A\n\n"+self.previous_messages, "author": 'bot', }]
