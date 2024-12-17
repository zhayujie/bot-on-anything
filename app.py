# encoding:utf-8

import argparse
import config
from channel import channel_factory
from common import log, const
from multiprocessing import Pool

from plugins.plugin_manager import PluginManager


# Start channel
def start_process(channel_type, config_path):
    try:
        # For multi-process startup, child processes cannot directly access parent process memory space, recreate config class
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
        # 1. For single string config format, start directly
        if not isinstance(channel_type, list):
            start_process(channel_type, args.config)
            exit(0)

        # 2. For single channel list config, start directly
        if len(channel_type) == 1:
            start_process(channel_type[0], args.config)
            exit(0)

        # 3. For multi-channel config, start with process pool
        # Use main process to start terminal channel
        if const.TERMINAL in channel_type:
            index = channel_type.index(const.TERMINAL)
            terminal = channel_type.pop(index)
        else:
            terminal = None

        # Use process pool to start other channel subprocesses
        pool = Pool(len(channel_type))
        for type_item in channel_type:
            log.info("[INIT] Start up: {} on {}", model_type, type_item)
            pool.apply_async(start_process, args=[type_item, args.config])

        if terminal:
            start_process(terminal, args.config)

        # Wait for all processes in the pool to complete
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
