from typing import Union,Any,Callable
from azent.core import Agent
from azent.core import Result,DeepseekResult
from azent.core.context_manager import ContextManager
from azent.core.run_context import RunContext
from azent.core.message import HumanMessage,BaseMessage

class HumanFeedBackResult(Result):

    def __init__(self, response,message:BaseMessage|None = None):
        super().__init__(response)
        type:str = "human_feedback_result"
        if isinstance(response,str):
              message = HumanMessage(content=message)
        else:
            if response is None and message:
                message = message
        self.messages = [message]
    def get_data(self):
        return self.messages[0]
    
    def get_message(self):
         return self.messages
    
    def get_text(self):
         return self.messages[0].content

class UserProxyAgent:
    def __init__(self,name,query_handle:Callable[...,Result]):
        self.name = name
        self.query_handle = query_handle

    def sync_run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:RunContext|None=None)->Result[Any]:

            return self.query_handle(query)

        