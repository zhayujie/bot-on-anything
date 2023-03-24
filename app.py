# encoding:utf-8

import config
from channel import channel_factory
from common import log, const
from multiprocessing import Pool


# 启动通道
def start_process(channel_type):
    # 若为多进程启动,子进程无法直接访问主进程的内存空间,重新创建config类
    config.load_config()
    model_type = config.conf().get("model").get("type")
    log.info("[INIT] Start up: {} on {}", model_type, channel_type)

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

        # 1.单个字符串格式配置时，直接启动
        if not isinstance(channel_type, list):
            start_process(channel_type)
            exit(0)

        # 2.单通道列表配置时，直接启动
        if len(channel_type) == 1:
            start_process(channel_type[0])
            exit(0)

        # 3.多通道配置时，进程池启动
        # 使用主进程启动终端通道
        if const.TERMINAL in channel_type:
            index = channel_type.index(const.TERMINAL)
            terminal = channel_type.pop(index)
        else:
            terminal = None

        # 使用进程池启动其他通道子进程
        pool = Pool(len(channel_type))
        for type_item in channel_type:
            log.info("[INIT] Start up: {} on {}", model_type, type_item)
            pool.apply_async(start_process, args=[type_item])

        if terminal:
            start_process(terminal)

        # 等待池中所有进程执行完毕
        pool.close()
        pool.join()
    except Exception as e:
        log.error("App startup failed!")
        log.exception(e)
