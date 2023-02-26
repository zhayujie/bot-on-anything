# encoding:utf-8

import config
from channel import channel_factory
from common import log

if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        model_type = config.conf().get("model").get("type")
        channel_type = config.conf().get("channel").get("type")

        log.info("[INIT] Start up: {} on {}", model_type, channel_type)

        # create channel
        channel = channel_factory.create_channel(channel_type)

        # startup channel
        channel.startup()
    except Exception as e:
        log.error("App startup failed!")
        log.exception(e)
