from model import model_factory
import config

class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query, context):
        return model_factory.create_bot(config.conf().get("model").get("type")).reply(query, context)
