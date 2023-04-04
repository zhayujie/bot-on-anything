# encoding:utf-8

import json
import os

config = {}


def load_config(config_path = "./config.json"):
    global config
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')

    config_str = read_file(config_path)
    # 将json字符串反序列化为dict类型
    config = json.loads(config_str)
    print("Load config success")
    return config

def get_root():
    return os.path.dirname(os.path.abspath( __file__ ))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    return config


def model_conf(model_type):
    return config.get('model').get(model_type)

def model_conf_val(model_type, key):
    val = config.get('model').get(model_type).get(key)
    if not val:
        # common default config
        return config.get('model').get(key)
    return val


def channel_conf(channel_type):
    return config.get('channel').get(channel_type)


def channel_conf_val(channel_type, key, default=None):
    val = config.get('channel').get(channel_type).get(key)
    if not val:
        # common default config
        return config.get('channel').get(key, default)
    return val


def common_conf_val(key, default=None):
    if not config.get('common'):
        return default
    return config.get('common').get(key, default)
