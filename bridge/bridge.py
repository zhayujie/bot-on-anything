from model import model_factory
import config

class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query, context):
        return model_factory.create_bot(config.conf().get("model").get("type")).reply(query, context)

    async def fetch_reply_stream(self, query, context):
        bot=model_factory.create_bot(config.conf().get("model").get("type"))
        async for final,response in bot.reply_text_stream(query, context):
            yield final,response
