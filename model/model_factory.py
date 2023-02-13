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
        # OpenAI 官方对话模型API
        from model.openai.open_ai_model import OpenAIModel
        return OpenAIModel()

    raise RuntimeError
