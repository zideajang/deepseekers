from deepseekers.core import Client

from ollama import ChatResponse, chat

# 默认的 Client
class OllamaClient(Client):
    def __init__(self, 
                 name:str,
                 ):
        super().__init__(name, None, None)

        
    def chat(self,config):
        # TODO 优化对于 Config 进行 constraints 或者给与类型
        response = chat(**config)
        return response