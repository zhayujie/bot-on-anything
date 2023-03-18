# encoding:utf-8

import config
from channel import channel_factory
from common import log
from multiprocessing import Process

def startProcess(channel_type):
        # create channel
        channel = channel_factory.create_channel(channel_type)
        # startup channel
        channel.startup()

if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        model_type = config.conf().get("model").get("type")
        channel_type = config.conf().get("channel").get("type")

        for type in channel_type:
            log.info("[INIT] Start up: {} on {}", model_type, type)
            p = Process(target=startProcess, args=(type))
            p.start()
    except Exception as e:
        log.error("App startup failed!")
        log.exception(e)