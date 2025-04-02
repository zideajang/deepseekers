import os
import time
import pickle
import hashlib
from typing import Union,Optional
from deepseekers.core.client import ClientConfig
class RunContext[T]:
    def __init__(self,
                 deps:Optional[T] = None,
                 config:Optional[ClientConfig] = None,
                 cache_dir:str = None
                 ):
        self.deps:Union[T,None] = deps 
        self.config = config
        self.is_cache = False
        if cache_dir:
            self.cache_dir = cache_dir 
            self.is_cache = True
    def _get_message_hash(self, message: dict) -> str:
        """计算消息内容的哈希值并返回前 6 位。"""
        content = message.get('content', '')
        encoded_content = content.encode('utf-8')
        return hashlib.sha256(encoded_content).hexdigest()[:6]

    def load_response(self,messages,agent_name):
        if not self.is_cache or not messages:
            return None

        message_hash = self._get_message_hash(messages[-1])
        pattern = f"{self.cache_dir}/{agent_name}_{message_hash}_*.pkl"
        import glob
        cached_files = glob.glob(pattern)

        if not cached_files:
            return None

        # 找到最近修改的文件
        latest_file = max(cached_files, key=os.path.getmtime)

        try:
            with open(latest_file, 'rb') as file:
                cached_data = pickle.load(file)
            return cached_data
        except Exception as e:
            print(f"加载缓存文件失败: {latest_file}, 错误: {e}")
            return None

    def save_response(self,response,messages,agent_name):

        if not self.is_cache or not self.cache_dir or not messages:
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        message_hash = self._get_message_hash(messages[-1])

        filename = f'{self.cache_dir}/{agent_name}_{message_hash}_{timestamp}.pkl'
        try:
            with open(filename, 'wb') as file:
                pickle.dump({"messages": messages, "response": response}, file)
        except Exception as e:
            print(f"保存缓存文件失败: {filename}, 错误: {e}")
    