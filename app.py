# encoding:utf-8

import config
from channel import channel_factory
from common import log
from multiprocessing import Pool

def startProcess(channel_type):
    # load config
    config.load_config()
    # create channel
    channel = channel_factory.create_channel(channel_type)
    # startup channel
    channel.startup()

def wrapper(channel_type):
    startProcess(channel_type)

if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        model_type = config.conf().get("model").get("type")
        channel_type = config.conf().get("channel").get("type")

        # 使用进程池启动子进程
        pool = Pool(len(channel_type))

        for type in channel_type:
            log.info("[INIT] Start up: {} on {}", model_type, type)
            pool.apply_async(wrapper, args=[type])

        # 等待池中所有进程执行完毕
        pool.close()
        pool.join()
    except Exception as e:
        log.error("App startup failed!")
        log.exception(e)