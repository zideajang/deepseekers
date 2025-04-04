import yaml
from abc import ABC,abstractmethod
from typing import TypedDict,Optional,Dict,List,Literal,LiteralString
from openai import OpenAI,AsyncClient
from azent.core.message import MessageDict

from azent.core.constants import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL
)

class ClientConfig(TypedDict,total=False):
    model:str
    messages:List[MessageDict]
    stream:Optional[bool]
    response_format:Optional[dict]
    tools:Optional[List[dict]]
    prompt:Optional[str]
    suffix:Optional[str]
    max_tokens:Optional[int]

class Client(ABC):
    """Client 抽象类，提供名称、API 密钥和 base URL"""
    def __init__(self,
                 name:str,
                 api_key:str,
                 base_url:str):
        """
        Args:
            name (str): 客户端的名称。
            api_key (Optional[str]): DeepSeek API 的密钥。默认为环境变量 DEEPSEEK_API_KEY。
            base_url (Optional[str]): DeepSeek API 的基础 URL。默认为环境变量 DEEPSEEK_BASE_URL 或 "https://api.deepseek.com/v1"。
            client (OpenAI): OpenAI 客户端实例，用于与 DeepSeek API 交互。
        """
        self.name:str = name
        self.api_key:str = api_key
        self.base_url:str = base_url

    @abstractmethod
    def chat(self,config:ClientConfig):
        raise ImportError()
    
    @abstractmethod
    async def async_chat(self,config:ClientConfig):
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
    
        
    def chat(self,config:ClientConfig):
        response = self.client.chat.completions.create(**config)
        return response
    
    async def async_chat(self, config):
        self.client = AsyncClient(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        response = await self.client.chat.completions.create(**config)
        return response
        
        print("暂时还没有实现...")
    

