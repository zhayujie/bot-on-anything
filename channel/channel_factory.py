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
    if channel_type== const.TERMINAL:
        from channel.terminal.terminal_channel import TerminalChannel
        return TerminalChannel()

    if channel_type == const.WECHAT:
        from channel.wechat.wechat_channel import WechatChannel
        return WechatChannel()

    elif channel_type == const.WECHAT_MP:
        from channel.wechat.wechat_mp_channel import WechatSubsribeAccount
        return WechatSubsribeAccount()

    elif channel_type == const.WECHAT_MP_SERVICE:
        from channel.wechat.wechat_mp_service_channel import WechatServiceAccount
        return WechatServiceAccount()

    elif channel_type == const.WECHAT_COM:
        from channel.wechat.wechat_com_channel import WechatEnterpriseChannel
        return WechatEnterpriseChannel()

    elif channel_type == const.QQ:
        from channel.qq.qq_channel import QQChannel
        return QQChannel()

    elif channel_type == const.GMAIL:
        from channel.gmail.gmail_channel import GmailChannel
        return GmailChannel()

    elif channel_type == const.TELEGRAM:
        from channel.telegram.telegram_channel import TelegramChannel
        return TelegramChannel()
    
    elif channel_type == const.SLACK:
        from channel.slack.slack_channel import SlackChannel
        return SlackChannel()

    elif channel_type == const.HTTP:
        from channel.http.http_channel import HttpChannel
        return HttpChannel()

    elif channel_type == const.DINGTALK:
        from channel.dingtalk.dingtalk_channel import DingTalkChannel
        return DingTalkChannel()

    elif channel_type == const.FEISHU:
        from channel.feishu.feishu_channel import FeiShuChannel
        return FeiShuChannel()

    elif channel_type == const.DISCORD:
        from channel.discord.discord_channel import DiscordChannel
        return DiscordChannel()

    else:
        raise RuntimeError("unknown channel_type in config.json: " + channel_type)
