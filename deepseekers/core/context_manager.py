from abc import ABC,abstractmethod
from typing import List,Protocol

class ContextManager(Protocol):

    def set(self, key, value):
        ...
    def get(self, key):
        ...

class DefaultContextManager:
    def __init__(self, callback=None):
        self._data = {}  # 内部字典存储数据
        self._callback = callback  # 回调函数

    def set(self, key, value):
        self._data[key] = value
        if self._callback:
            self._callback("set", key, value)  # 触发回调

    def get(self, key):
        value = self._data.get(key)
        if self._callback:
            self._callback("get", key, value)  # 触发回调
        return value

    def __setitem__(self, key, value):
        self.set(key, value)  # 兼容字典的设置语法

    def __getitem__(self, key):
        return self.get(key)  # 兼容字典的获取语法


