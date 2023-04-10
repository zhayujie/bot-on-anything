import json
import os
import re
from common import log

def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

def load_json_file(curdir: str, file: str = 'config.json'):
    config_path = os.path.join(curdir, file)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            log.warn(
                f"[common]load json file failed, {config_path}\{file} not found")
        else:
            log.warn("[common]load json file failed")
        raise e


def contain_chinese(str):
    """
    判断一个字符串中是否含有中文
    """
    pattern = re.compile('[\u4e00-\u9fa5]')
    match = pattern.search(str)
    return match != None


def check_prefix(content, prefix_list):
    if(len(prefix_list)==0):
        return True
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return False
