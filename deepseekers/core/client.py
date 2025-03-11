from abc import ABC,abstractmethod
import yaml
from typing import Any
from openai import OpenAI

# zideajang/deepseekers

# 获取 deepseek API
def get_config():
    with open("D:/config.yaml","r") as file:
        config = yaml.safe_load(file)
    return config

DEEPSEEK_API_KEY = get_config()['DEEPSEEK_API_KEY']
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'

class Client(ABC):
    def __init__(self,
                 name:str,
                 api_key:str,
                 base_url:str):
        
        self.name:str = name
        self.api_key:str = api_key
        self.base_url:str = base_url

    @abstractmethod
    def chat(self,config:Any):
        raise ImportError()
    
# 默认的 Client
class DeepSeekClient(Client):
    def __init__(self, 
                 name:str,
                 api_key = DEEPSEEK_API_KEY,
                 base_url = DEEPSEEK_BASE_URL
                 ):
        
        super().__init__(name, api_key, base_url)

        # TODO 连接是否正常
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
    def chat(self,config):
        # TODO 优化对于 Config 进行 constraints 或者给与类型
        response = self.client.chat.completions.create(**config)
        return response