from typing import Union, List, Dict,Callable,Protocol,Any,Literal
from rich.console import Console
import pandas as pd
from pydantic import BaseModel,Field
from deepseekers.core import Agent,Result
from deepseekers.core.message import HumanMessage
from deepseekers.core.run_context import RunContext

console = Console()

from .base import (BaseProvider,
                   BaseProviderContext,
                   BaseProviderResponse)

def modify_function_schema(func_schema_dict: dict) -> dict:
    """
    修改函数 schema 字典，移除 'context' 相关的 properties 和 required 字段。

    Args:
        func_schema_dict: 包含函数 schema 的字典。

    Returns:
        修改后的函数 schema 字典。
    """
    modified_schema = func_schema_dict.copy()

    if 'function' in modified_schema and 'parameters' in modified_schema['function']:
        parameters = modified_schema['function']['parameters']
        if 'properties' in parameters and 'context' in parameters['properties']:
            del parameters['properties']['context']

        if 'required' in parameters and 'context' in parameters['required']:
            parameters['required'].remove('context')
            # 如果 required 列表为空，也可以选择删除该键
            if not parameters['required']:
                del parameters['required']

    return modified_schema

class ProviderAction:
    pass


class AgentWrapper[D,T:BaseProvider]:
    def __init__(self,
                 agent:Agent,
                 provider:BaseProvider):
        self.name = f"{agent.name}_wrapper"
        self.agent = agent
        self.provider:T = provider

    def sync_run(self,
        query:Union[str,HumanMessage],
        # TODO 有待考量具体设计
        run_context:RunContext|None=None)->Result[Any]:
        result = self.agent.sync_run(query=query,run_context=RunContext(config={"tools":self.provider.tools}))
        action_dict = self.provider.extract_command(result=result)
        console.print(action_dict)
        console.print(result.get_message()[0])

        console.print(result)

