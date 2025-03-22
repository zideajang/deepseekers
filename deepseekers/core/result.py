import json
from abc import ABC,abstractmethod
from typing import TypeVar,Any,List,Dict,Union
from deepseekers.core.message import BaseMessage,AIMessage,ToolMessage

# ResultDataT = TypeVar(
#     "ResultDataT", default=str, covariant=True
# )

class Result[T](ABC):

    def __init__(self,response):
        self.response = response
        self.result_message = "空消息"

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
    def __init__(self, 
                 response:Any,
                messages:List[BaseMessage],
                 result_type=None):
        self.messages =  messages or []
        self.response = response
        self.result_type = result_type

        # print(self.response)

        if self.response.choices[0].message.content:
            self.result_message =  AIMessage(content=self.response.choices[0].message.content)

        elif self.response.choices[0].message.tool_calls:
            tool_call = self.response.choices[0].message.tool_calls[0]
            self.result_message = ToolMessage(tool_call=tool_call,
                        tool_id=tool_call.id,
                        tool_arguments=tool_call.function.arguments,
                        tool_name=tool_call.function.name,
                        content="")

        self.messages.append(self.result_message)

    @property
    def all_messages(self):
        return self.messages 

    def get_message(self):
        return [self.result_message]
    
    def get_text(self):
        return str(self.response.choices[0].message.content)

    def get_data(self)->T:
        if self.result_type:
            try:
                if not self.response.choices:
                    raise ValueError("No choices in response")
                print(self.response.choices[0].message.content)
                data = json.loads(self.response.choices[0].message.content)
                print(data)
                return self.result_type(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Error getting data: {e}")
                return None 
            
        else:
            return self.get_text()
        
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