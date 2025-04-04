import json
from typing import List,Any
from azent.core import Result,BaseMessage
from azent.core.message import AIMessage,ToolMessage

class OllamaResult[T](Result):
    def __init__(self, 
                 response:Any,
                messages:List[BaseMessage],
                 result_type=None):
        self.messages =  messages or []
        self.response = response
        self.result_type = result_type

        if self.response.message.content:
            self.result_message =  [AIMessage(content=self.response.message.content)]
        
        elif response.message.tool_calls:
            self.result_message = []
            for tool_call in response.message.tool_calls:
            #     if function_to_call := available_functions.get(tool.function.name):
            #         print('Calling function:', tool.function.name)
            #         print('Arguments:', tool.function.arguments)
            #         output = function_to_call(**tool.function.arguments)
            #         print('Function output:', output)
            #     else:
            #         print('Function', tool.function.name, 'not found')
            # tool_call = self.response.choices[0].message.tool_calls[0]
                self.result_message.append(ToolMessage(tool_call=tool_call,
                            tool_id= None,
                            tool_arguments=tool_call.function.arguments,
                            tool_name=tool_call.function.name,
                            content=""))

        self.messages.extend(self.result_message)

    @property
    def all_messages(self):
        return self.messages 

    def get_message(self):
        return self.result_message
    
    def get_text(self):
        return str(self.response.message.content)

    def get_data(self)->T:
        if self.result_type:
            try:
                if not self.response.choices:
                    raise ValueError("No choices in response")
                data = json.loads(self.response.message.content)
                return self.result_type(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Error getting data: {e}")
                return None 
            
        else:
            return self.get_text()