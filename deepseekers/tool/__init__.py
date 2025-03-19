import json
from typing import get_origin,List,Optional
from deepseekers.core import Agent,Result
from deepseekers.core.message import BaseMessage,ToolMessage,AIMessage
from deepseekers.context_manager import EventManager,EventType
from deepseekers.prompt.prompt_prefix import tool_call_result_prompt_template
def result_process(
        agent:Agent,
        result:Result,
        cb:Optional[EventManager]=None,
        auto_call_agent:bool=True):
    
    messages = result.get_message()
    if not isinstance(messages,List):
        raise TypeError(f"result:{type(messages)} is not List[BaseMessage]")
    message = result.get_message()[0]
    if isinstance(message,ToolMessage):
        # 开始调用工具时触发事件
        cb.trigger_event(EventType.OnStartToolCall,message)
        tool_calling_result = agent.available_tools[message.tool_name](**json.loads(message.tool_arguments))
        # 结束工具调用时触发事件
        if auto_call_agent:
            prompt = tool_call_result_prompt_template(message.tool_name,
                                             tool_calling_result,
                                             agent.messages[-1].content)

            response = agent.run(prompt)
        else:
            response = tool_calling_result
        cb.trigger_event(EventType.OnEndToolCall,response)

        if isinstance(response,str):
            cb.trigger_event(EventType.OnResponse,AIMessage(content=response))
        elif isinstance(response,Result):
            cb.trigger_event(EventType.OnResponse,AIMessage(content=response.get_text()))
        else:
            cb.trigger_event(EventType.OnResponse,AIMessage(content=json.dumps(response)))
    else:
        cb.trigger_event(EventType.OnResponse,message)