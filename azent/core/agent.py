import os
import time
import json
from abc import ABC
import types

from typing import Protocol
import asyncio

from typing import Dict,Any,Union,Optional,List,Callable
from functools import wraps

from rich.console import Console
from rich.panel import Panel

from azent.core import Client,DeepSeekClient
from azent.core.context_manager import ContextManager
from azent.core.message import SystemMessage,AIMessage,HumanMessage,BaseMessage,MessageRole
from azent.core.message import MessageDict

from azent.core.result import Result,ErrorResult,DeepseekResult
from azent.core.utils import _json_schema_to_example,function_to_json
from azent.core.mytypes import ResponseOrError

from azent.core.constants import __CTX_VARS_NAME__

from azent.core.message_manager import MessageManager
from azent.core.tool_manager import ToolManager
from azent.core.run_context import RunContext
from azent.core.client import ClientConfig

console = Console()

class AgentLifeCycleInterface(Protocol):
    def on_bind_tool(self,tool_name):
        ...

    def on_unbind_tool(self,tool_name):
        ...

    def on_before_tool_call(self,tool_name,tool_arguments):
        ...

    def on_after_tool_call(self,tool_name,tool_arguments):
        ...
    def on_before_run_agent(self,messages):
        ...

    def on_afater_run_agent(self,messages):
        ...

class AgentLifeCycle:
    def __init__(self,agent:"Agent"):
        self.agent:"Agent" = agent
        self.agent.lifecycle = self


def chat(f):
    return f()

def async_chat(func):
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

class AgentDep:
    pass


# class RunConext
ContextType = Optional[Union[Dict[str,Any],Callable[...,Dict[str,Any]],ContextManager]]

        
class Agent[D,T:Result](ABC):
    """Agent 类,具有自主性智能体"""
    def __init__(self,
            name:str,
            description:str|None = None,
            client:Optional[Client] = DeepSeekClient(name='deepseek-client'),
            model_name:Optional[str] = 'deepseek-chat',
            system_message:Optional[Union[str,SystemMessage,Callable[...,Union[str,SystemMessage]]]] = None,
            # DONE 这是一次代价不小的改动，不过这次改动的是值得的，让参数名字更加明确了，不会因为名字产生不必要误会
            result_data_type:Optional[type]= None,
            result_type:Optional[type] = None,

            handoffs:Optional[List["Agent"]]=None,
            handoff_description:Optional[str|Callable[...,str]] = None,
            
            # 将工具的管理和消息的管理交给外部，以接口形式让 tool_manager 和 message_manager 
            # 可以和 Agent 解耦
            tool_manager:ToolManager|None = None,
            message_manager:ToolManager|None = None,
            life_cycle:Optional[AgentLifeCycleInterface] = None
        ):
        
        """
        Args:
            mane(str): Agent 的名称，name 命名规范，snake 方式进行，是 Agent 的一个标识
            description(str): Agent 进行概括性的描述以及说明
            client:(Client): 默认的就是 DeepSeek
            result_data_type:Optional[type]= None,
            result_type:Optional[type] = None,
        """
        self.name:str = name
        self.description = description or self.name
        self.client:Client = client
        
        self.config:ClientConfig = {
            "model":model_name,
        }

        # 默认支持 DeepseekResult
        self.result_type:type = result_type or DeepseekResult
        self.result_data_type:type = result_data_type
        # 狠心地抛弃了 self.context ，一起都是变为运行时的 context
        self.context = {}            
        # TODO 以后还会进行进一步扩展 
        # - 可用工具 check tool_name 是不是可用，
        # - 该工具是否为授权工具，如果不是授权工具，执行需要用户确认
        self.available_tools:Dict[str,Callable] = {}


        self.handoff_description = handoff_description
        # TODO 随后可能需要将 DefaultMessageManager 来替换 MessageManager 
        # MessageManager 作为接口类
        self.message_manager = message_manager or MessageManager(system_message=system_message)
        
        if result_data_type:
            if isinstance(result_data_type, types.GenericAlias):
                origin = result_data_type.__origin__
                args = result_data_type.__args__
                if origin is list and args:
                    result_data_type = args[0]
                    self.message_manager.add_message(SystemMessage(content=f'\nEXAMPLE JSON OUTPUT:\n{{"items":[{json.loads(_json_schema_to_example(result_data_type=result_data_type,is_flag=False).replace("'",'"'))}]}}'.replace("'",'"') ))
                else:
                    print("无法从 GenericAlias 中提取类型。")
            else :
                self.message_manager.add_message(SystemMessage(content=_json_schema_to_example(result_data_type=result_data_type)))
        

        if handoffs:
            self.handoffs_dict = {}
            system_message_content = ""
            for agent in handoffs:
                self.handoffs_dict[agent.name] = agent
                if agent.handoff_description is None:
                    raise ValueError(f"需要初始化 {self.handoff_description}")
                system_message_content += f"""
{agent.name}
{agent.handoff_description}
"""         
            self.message_manager.add_message(SystemMessage(content=system_message_content))

        # 初始化智能工具
        if tool_manager:
            self.tool_manager = tool_manager
        else:
            self.tool_manager = ToolManager(self)

        self.life_cycle = life_cycle

    def update_handoff_description(self,handoff_description):
        self.handoff_description = handoff_description
    
    def tool(self,func):
        self.bind_tool(func.__name__,func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            # self.available_tools[tool_name if tool_name else func.__name__] = func
            # TODO
            result = func(*args, **kwargs)
            return result
        return wrapper
    
    def tool_with_context(self,func):
        self.bind_tool(func.__name__,func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            # self.available_tools[tool_name if tool_name else func.__name__] = func
            # TODO
            result = func(self.context,*args, **kwargs)
            return result
        return wrapper


    # 绑定工具
    def bind_tool(self,tool_name:str,func:Callable,is_async:bool=False):
        self.tool_manager.add_tool(tool_name,func,is_async=is_async)

    # 解除工具绑定
    def unbind_tool(self,func):
        self.tool_manager.remove_tool(func)      
    
    def add_message(self,message:str|MessageDict|BaseMessage):
        self.message_manager.add_message(message)
    
    def messages_to_dict(self)-> List:
        return self.message_manager.to_dict(self.context)
    
    async def before_run(self,query:Union[str,HumanMessage],
            run_context:RunContext|None=None):
        
        self.add_message(query)
        # 一定要先于 message
        if run_context and run_context.deps:
            self.context['deps'] = run_context.deps

        messages = self.messages_to_dict()
        tools = self.tool_manager.tools
        self.config["messages"] = messages
        
        if tools:
            self.config["tools"] = tools

        if run_context and hasattr(run_context,"config") and run_context.config and "tools" in run_context.config:
            if 'tools' not in self.config:
                self.config["tools"] = run_context.config['tools']
            else:
                self.config["tools"].extend(run_context.config['tools'])        
        if self.result_data_type:
            self.config['response_format'] = {
                'type': 'json_object'
            }

    def sync_run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:RunContext|None=None)->Result[Any]:
        return asyncio.run(self.run(query,run_context))

    async def run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:RunContext[D]|None=None)->Result:
        
        await self.before_run(query,run_context)

        for message in self.config["messages"]:
            console.print(Panel(message['content'],title=message['role']),style="cyan")
        console.print(f"{self.message_manager.total_token}",style="green bold",justify="center")
        @async_chat
        async def get_result()->ResponseOrError:
            try:
                if run_context and run_context.is_cache:
                    cached_data = run_context.load_response(messages=self.config["messages"],agent_name=self.name)
                    if cached_data:
                        response = cached_data['response']
                    else:
                        response = await self.client.async_chat(self.config)
                        run_context.save_response(messages=self.config["messages"],agent_name=self.name)
                else:
                    # print(self.config)
                    response = await self.client.async_chat(self.config)
                    # print(response)
                return ResponseOrError.from_response(response)
            except Exception as e:
                return ResponseOrError.from_error(e)
        result = await get_result()

        if result.is_ok():
            response = result.unwrap()
            res:T = self.result_type(response=response,
                                 messages=self.message_manager.messages,
                                 result_data_type=self.result_data_type)
            
            if hasattr(self, 'handoffs_dict') and self.handoffs_dict:
                # TODO
                result_data = res.get_data()
                if hasattr(result_data, 'agent_name'):
                    if result_data.agent_name in self.handoffs_dict:
                        if isinstance(query,str):
                            res_again = self.handoffs_dict[result_data.agent_name].run(HumanMessage(content=query))
                        else:
                            res_again = self.handoffs_dict[result_data.agent_name].run(query)
                        return res_again
                    
            return res 
        else:
            error = result.error
            return ErrorResult(response=error)


    def __str__(self):
        return f"""
Hey I am {self.name}
Clent: {self.client.name}
{'-'*20}
system message: \n
{self.message_manager.messages[0]}
{[ tool['function']['name'] for tool in self.available_tools ] if self.available_tools else "暂时没有提供任何工具"}
"""
    