from typing import Optional,Callable,List
from deepseekers.core import Agent

def handoff(agent:Agent,
            handoff_description:str,
            tools:Optional[List[Callable]]=None,
            ):
    
    agent.handoff_description = handoff_description
    if tools:
        agent.bind_tools(tools)
    return agent

