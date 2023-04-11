# encoding:utf-8

import argparse
import config
from channel import channel_factory
from common import log, const
from multiprocessing import Pool

from plugins.plugin_manager import PluginManager


# 启动通道
def start_process(channel_type, config_path):
    try:
        # 若为多进程启动,子进程无法直接访问主进程的内存空间,重新创建config类
        config.load_config(config_path)
        model_type = config.conf().get("model").get("type")
        log.info("[MultiChannel] Start up {} on {}", model_type, channel_type)
        channel = channel_factory.create_channel(channel_type)
        channel.startup()
    except Exception as e:
        log.error("[MultiChannel] Start up failed on {}: {}", channel_type, str(e))
        raise e


def main():
    try:
        # load config
        config.load_config(args.config)

        model_type = config.conf().get("model").get("type")
        channel_type = config.conf().get("channel").get("type")

        PluginManager()
        # 1.单个字符串格式配置时，直接启动
        if not isinstance(channel_type, list):
            start_process(channel_type, args.config)
            exit(0)

        # 2.单通道列表配置时，直接启动
        if len(channel_type) == 1:
            start_process(channel_type[0], args.config)
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
            pool.apply_async(start_process, args=[type_item, args.config])

        if terminal:
            start_process(terminal, args.config)

        # 等待池中所有进程执行完毕
        pool.close()
        pool.join()
    except Exception as e:
        log.error("App startup failed!")
        log.exception(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="config.json path(e.g: ./config.json  or  /usr/local/bot-on-anything/config.json)",type=str,default="./config.json")
    args = parser.parse_args()
    main()
