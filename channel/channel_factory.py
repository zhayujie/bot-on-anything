"""
channel factory
"""
from common import const

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == const.WECHAT:
        from channel.wechat.wechat_channel import WechatChannel
        return WechatChannel()

    elif channel_type == const.WECHAT_MP:
        from channel.wechat.wechat_mp_channel import WechatPublicAccount
        return WechatPublicAccount()

    else:
        raise RuntimeError
