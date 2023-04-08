"""
channel factory
"""

from common import const

def create_bot(model_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """

    if model_type == const.OPEN_AI:
        # OpenAI 官方对话模型API (gpt-3.0)
        from model.openai.open_ai_model import OpenAIModel
        return OpenAIModel()

    elif model_type == const.CHATGPT:
        # ChatGPT API (gpt-3.5-turbo)
        from model.openai.chatgpt_model import ChatGPTModel
        return ChatGPTModel()

    elif model_type == const.BAIDU:
        from model.baidu.yiyan_model import YiyanModel
        return YiyanModel()

    elif model_type == const.BING:
        from model.bing.new_bing_model import BingModel
        return BingModel()

    elif model_type == const.BARD:
        from model.google.bard_model import BardModel
        return BardModel()

    raise RuntimeError
