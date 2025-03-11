import json
from abc import ABC,abstractmethod

from deepseekers.core.message import BaseMessage,AIMessage

class Result[T](ABC):

    def __init__(self,response):
        self.response = response

    @abstractmethod
    def get_message(self)->BaseMessage:
        raise NotImplementedError()

    @abstractmethod
    def get_text(self)->str:
        raise NotImplementedError()

    @abstractmethod
    def get_data(self)->T:
        raise NotImplementedError()
    


class DeepseekResult[T](Result):
    def __init__(self, response,result_type=None):
        self.response = response
        self.result_type = result_type

    def get_message(self):
        return AIMessage(content=self.response.choices[0].message.content)
    
    def get_text(self):
        return str(self.response.choices[0].message.content)
    
    def get_data(self)->T:
        return self.result_type(**json.loads(self.response.choices[0].message.content))

class ErrorResult(Result):
    def __init__(self,  response):
        super().__init__(response)
        self.response = response
    def get_message(self):
        return AIMessage(content=self.response)
    def get_text(self):
        return self.response
    # TODO clientError
    def get_data(self):
        return self.response