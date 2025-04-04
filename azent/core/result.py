import types
import json
import re
from abc import ABC,abstractmethod
from pydantic import BaseModel
from typing import TypeVar,Any,List,Dict,Union
from azent.core.message import BaseMessage,AIMessage,ToolMessage

# ResultDataT = TypeVar(
#     "ResultDataT", default=str, covariant=True
# )



class Result[T](ABC):

    def __init__(self,response):
        self.response = response
        self.result_message = "空消息"
        self.messages = []

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
                 result_data_type=None):
        self.messages =  messages or []
        self.response = response
        self.result_data_type = result_data_type

        # print(self.response)

        if self.response.choices[0].message.content:
            self.result_message =  AIMessage(content=self.response.choices[0].message.content)

        elif self.response.choices[0].message.tool_calls:
            for tool_call in self.response.choices[0].message.tool_calls:
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

        if isinstance(self.result_data_type, types.GenericAlias):
            origin = self.result_data_type.__origin__
            args = self.result_data_type.__args__
            if origin is list and args:
                result_data_type = args[0]
                
            data = json.loads(self.response.choices[0].message.content)
            try:
                return [result_data_type(**item) for item in data['items']]
            except:
                try:
                    
                    match = re.search(r"'(.*?)'", f"{args[0]}")
                    if match:
                        result_data_type_string = match.group(1)  # 获取括号内的内容
                        result_data_type_string = result_data_type_string.lower()
                        print(result_data_type_string)
                        return [result_data_type(**item) for item in data[f"{result_data_type_string}"]]
                    else:
                        return data
                except:
                    return data
                
            
            
        elif self.result_data_type:
            try:
                if not self.response.choices:
                    raise ValueError("No choices in response")
                data = json.loads(self.response.choices[0].message.content)
                return self.result_data_type(**data)
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