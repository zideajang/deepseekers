import json
import asyncio
from typing import get_origin,List,Optional
from azent.core import Agent,Result
from azent.core.message import BaseMessage,ToolMessage,AIMessage
from azent.context_manager import EventManager,EventType
from azent.prompt.prompt_prefix import tool_call_result_prompt_template

def sync_function():
    return asyncio.get_event_loop().run_until_complete(my_coroutine())

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
        def sync_wrapper():
            # 创建新事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)  # 设置为当前线程的事件循环
            try:
                result = loop.run_until_complete(agent.tool_manager.execute_tool(message))
            finally:
                loop.close()  # 关闭事件循环
            return result
        tool_calling_result = sync_wrapper()
        print(tool_calling_result)
        print("---"*20)
        # 结束工具调用时触发事件
        if auto_call_agent:
            prompt = tool_call_result_prompt_template(message.tool_name,
                                             tool_calling_result,
                                             agent.messages[-1].content)

            response = agent.sync_run(prompt)
        else:
            response = tool_calling_result
        cb.trigger_event(EventType.OnEndToolCall,response)

        if isinstance(response,str):
            cb.trigger_event(EventType.OnResponse,AIMessage(content=response))
        elif isinstance(response,Result):
            cb.trigger_event(EventType.OnResponse,AIMessage(content=response.get_text()))
        else:
            pass
            # cb.trigger_event(EventType.OnResponse,AIMessage(content=json.dumps(response)))
    else:
        cb.trigger_event(EventType.OnResponse,message)