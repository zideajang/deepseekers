from functools import wraps
from typing import Optional,Callable,List
from azent.core import Agent
from azent.core.message import HumanMessage

def handoff(agent:Agent,
            handoff_description:str,
            tools:Optional[List[Callable]]=None,
            ):
    
    agent.handoff_description = handoff_description
    if tools and isinstance(tools,list):
        for tool in tools:
            agent.bind_tool(tool)
    return agent


def handoff_with_tool(agent:Agent,on_handoff):
    def decorator(func:Callable[...,str]):
        @wraps(func)
        def wrapper(*args,**kwargs):
            # 打印 agent
            on_handoff(agent.name)
            result = func(*args,**kwargs)
            # TODO 返回 result
            result = agent.run(HumanMessage(content=agent.messages[-1].content + result))
            return result
        return wrapper
    return decorator

