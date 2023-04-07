# -*- coding: UTF-8 -*-

import time
from threading import Lock


class Store(object):
    """
    This is an interface to storage (Key, Value) pairs for sdk.
    """

    def get(self, key):  # type: (str) -> Tuple[bool, str]
        return False, ''

    def set(self, key, value, expire):  # type: (str, str, int) -> None
        """
        storage key, value into the store, value has an expire time.(unit: second)
        """
        pass


class ExpireValue(object):
    def __init__(self, value, expireTime):  # type: (str, int) -> None
        self.value = value
        self.expireTime = expireTime


class MemoryStore(Store):
    """
    This is an implement of `StoreInterface` which stores data in the memory
    """

    def __init__(self):  # type: () -> None
        self.data = {}  # type: Dict[str, ExpireValue]
        self.mutex = Lock()  # type: Lock

    def get(self, key):  # type: (str) -> Tuple[bool, str]
        # print('get %s' % key)
        self.mutex.acquire()
        try:
            val = self.data.get(key)
            if val is None:
                return False, ""
            else:
                if val.expireTime == -1:
                    return True, val.value
                elif val.expireTime < int(time.time()):
                    self.data.pop(key)
                    return False, ""
                else:
                    return True, val.value
        finally:
            self.mutex.release()

    def set(self, key, value, expire=None):  # type: (str, str, int) -> None
        # print('put %s=%s, expire=%s' % (key, value, expire))
        """
        storage key, value into the store, value has an expire time.(unit: second)
        """
        self.mutex.acquire()
        try:
            self.data[key] = ExpireValue(
                value, expire == None and -1 or int(time.time()) + expire)
        finally:
            self.mutex.release()


