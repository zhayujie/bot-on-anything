import re


def contain_chinese(str):
    """
    判断一个字符串中是否含有中文
    """
    pattern = re.compile('[\u4e00-\u9fa5]')
    match = pattern.search(str)
    return match != None


def check_prefix(content, prefix_list):
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None