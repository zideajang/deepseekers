from abc import ABC
import inspect
from typing import Protocol
import pickle
import time

from typing import Dict,Any,Union,Optional,List,Callable
from functools import wraps
import inspect
from deepseekers.core import Client,DeepSeekClient
from deepseekers.core.context_manager import ContextManager
from deepseekers.core.message import SystemMessage,AIMessage,HumanMessage,BaseMessage,MessageRole

from deepseekers.core.result import Result,ErrorResult,DeepseekResult
from deepseekers.core.utils import _json_schema_to_example,print_config,function_to_json
from deepseekers.core.types import ResponseOrError
"""
# 
D: Depense -> 前奏，Agent 启动需要具备哪些，例如需要连接网络 
- http httpx.client 拿到 context 具备
- 对于数据库连接 ，http context 或者 database connec

T:Result 也就是返回数据结构，json Result<T> 来解析数据
"""



class AgentLifeCycleInterface(Protocol):
    def on_bind_tool(self,agent_name,tool_name):
        ...

    def on_tool_call(self,tool_name,tool_arguments):
        ...

    def on_end_tool_call(self,tool_name,tool_arguments):
        ...
    def on_run_agent(self):
        ...

    def on_end_run_agent(self):
        ...


class AgentLifeCycle:
    def __init__(self,agent:"Agent"):
        self.agent:"Agent" = agent
        self.agent.lifecycle = self


def chat(f):
    return f()

class AgentDep:
    pass

ContextType = Optional[Union[Dict[str,Any],Callable[...,Dict[str,Any]],ContextManager]]

__CTX_VARS_NAME__ = "context"

class Agent[D,T](ABC):
    def __init__(self,
                 name:str,
                 client:Optional[Client] = DeepSeekClient(name='deepseek-client'),
                 model_name:Optional[str] = 'deepseek-chat',
                 context:ContextType=None,
                #  TODO 以后 system message 增加支持模板类
                # 运行时可以动态传一些参数 system，systemplate.render()
                 system_message:Optional[Union[str,SystemMessage,Callable[...,Union[str,SystemMessage]]]] = None,
                
                 deps_type:Optional[type] = None,
                 result_type:Optional[type]= None,

                 handoffs:Optional[List["Agent"]]=None,
                 handoff_description:Optional[str|Callable[...,str]] = None,
                 lifecylce:Optional[AgentLifeCycleInterface] = None,
                 span:Optional[Any] = None,
                 verbose:bool = True,
                 is_debug=False
                ):
        
        """
Args:
        :param name: Agent 的名称
        :type name: str
        :param context: 上下文
"""
        
        # agnet name
        self.name:str = name
        # agent 客户端
        self.client:Client = client

        # 维护 messages ，记录 converstaion 发生所有 Message 包括 
        # HumanMessage,AIMessage,SystemMessage ...
        # 并不是参与到 chat 中的 message 会经过一次过滤，
        # 过滤条件就是 is_hidden
        self.messages:List[BaseMessage] = []

        self.ResultType:type = DeepseekResult

        self.verbose = verbose
        self.is_debug = is_debug
        self.model_name = model_name
        
        self.deps = None
        self.deps_type = deps_type
        # 共享上下文数据
        # TODO
        self.context = context or {}
        # 如果有依赖项，需要通过 context['deps'] 将依赖数据传入进来
        if self.deps_type:
            if 'deps' not in self.context.keys():
                raise ValueError("需要在 context 提供 deps 字段内容")
            self.deps = self.context['deps']
            
        # TODO 以后还会进行进一步扩展 
        # - 可用工具 check tool_name 是不是可用，
        # - 该工具是否为授权工具，如果不是授权工具，执行需要用户确认
        self.available_tools:Dict[str,Callable] = {}
        self.result_type = result_type
        self.system_message  = None
        self.lifecycle = lifecylce

        self.handoff_description = handoff_description
        
        if system_message:
            if isinstance(system_message,str):
                if result_type:
                    res = _json_schema_to_example(result_type=result_type)
                    self.add_message({
                        'role':'system',
                        'content':system_message + res
                    })
                else:
                    self.add_message({
                        'role':'system',
                        'content':system_message
                    })

            elif isinstance(system_message,SystemMessage):
                if result_type:
                    res = _json_schema_to_example(result_type=result_type)
                    system_message.content = system_message.content + res
                    self.add_message(system_message)

                else:
                    self.add_message(system_message)

            elif callable(system_message):
                self.add_message(system_message)
            

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
            if self.messages and isinstance(self.messages[0],BaseMessage):
                content = self.messages[0].content
                self.messages[0] = SystemMessage(content=content+system_message_content)
          
        if self.messages and isinstance(self.messages[0],BaseMessage):
            self.system_message = self.messages[0]

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
    # @property
    # def system_message(self):
    #     return self.messages[0] if self.messages[0] and isinstance(self.messages[0],SystemMessage) else None

    def bind_tools(self,tools):
        # TODO 需要进行校验
        for tool in tools:
            if callable(tool):
                self.bind_tool(tool.__name__,tool)

    def bind_tool(self,tool_name:str,func:Callable):
        # console.print("bind_tool")

        if self.lifecycle:
            self.lifecycle.on_bind_tool(self.name,tool_name)
        self.available_tools[tool_name if tool_name else func.__name__] = func

    def unbind_tool(self,func):
        self.available_tools.pop(func.__name__)
        # TODO 遍历 self.tools 中所有工具，删除目标对象
        # if len(self.tools) == 1:
        #     self.tools = []
        # elif len(self.tools) > 1:
        #     for i in range(len(self.tools)):
        #         if self.tools[i].name == func.__name__:
        #             del self.tools[i]
        # console.print(self.tools)        

    # TODO 动态注入 agent
    def system_prompt(self,**inject_kwargs):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                all_kwargs = {**inject_kwargs, **kwargs}
                func_code = str(func)
                # TODO 在运行时候希望在 Agent 自行调用
                prompt = func(self.context, *args, **all_kwargs)
                # prompt_hash = hashlib.sha256(prompt.encode()).hexdiges

                func_code = inspect.getsource(func)  # 获取函数的源代码
                func_signature = inspect.signature(func)  # 获取函数的签名

                # 获取函数的名字
                func_name = func.__name__
                # parameters = list(func_signature.parameters.keys())
                # timestr = time.strftime("%Y%m%d-%H%M%S")
                # prompt_id = hashlib.md5(func_code.encode()).hexdigest()
                # pormpt_dict ={
                #     "id":prompt_id,
                #     "name":func_name,
                #     "decription":func.__doc__,
                #     "code":func_code,
                #     "parameters": parameters,
                #     "model_name":self.model_name,
                #     "time":timestr
                # }
                # with open(f"./prompt_store_v2/{prompt_id}-{timestr}.pkl", "wb") as f:
                #     pickle.dump(pormpt_dict, f)
                self._update_system_message(prompt)
                return prompt
            return wrapper
        return decorator
    
    def result_validator(self,**inject_kwargs):
        pass

    def update_system_message(self,prompt):
        self.messages = []
        self._update_system_message(prompt)

    def _update_system_message(self,prompt:Union[str|BaseMessage]):
        if isinstance(prompt,str):
            self.system_message = SystemMessage(content=prompt)
        elif isinstance(prompt,BaseMessage):
            self.system_message = prompt
        else:
            raise ValueError(f"不支持 prompt 类型 {type(prompt)}, 类型应该为 string 或者 SystemMessge")
        
        if self.messages:
            self.messages[0] = self.system_message
        else:
            self.messages.append(self.system_message)

    # TODO python 成员函数对泛型的支持
    def add_message(self,message:Union[Dict,BaseMessage]):

        if isinstance(message,Dict):
            # TODO 检查 dict 的 shape
            message = BaseMessage(role=message['role'],content=message['content'])
        elif isinstance(message,BaseMessage):
            message = message

        elif isinstance(message,str):
            message = HumanMessage(content=message)
        elif callable(message):
            message = message
        else:
            raise ValueError(f"不支持 query 类型 {type(query)}, 类型应该为 string 或者 HumanSystem")
        self.messages.append(message)
        return message

    def messages_to_dict(self):
        res =[]
        for message in self.messages:
            if message.role in [MessageRole.AI,MessageRole.Human,MessageRole.System]:
                res.append(message.model_dump())
        return res
    
    def update_deps(self,deps_value):
        self.deps = deps_value
    def update_model_config(self,config):
        self.model_config = config
    def update_result(self,result):
        self.result = result

    def run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            deps:Dict[str,Any]=None)->Result:
        
        # 更新 dependence
        if deps:
            deps_value:D = deps.pop('deps', None)
            self.update_deps(deps_value)

        self.add_message(query)

        # 动态更新 deps
        if self.deps and callable(self.messages[0]):
            # self.messages[-1].content += self.deps.model_dump_json()
            self.messages[0] = self.messages[0](self.deps)
        
        messages = self.messages_to_dict()
        config = {
            "model":self.model_name,
            "messages":messages,
        }

        if deps:
            for k,v in deps.items():
                config[k] = v

        
        # TODO
        # 更新工具
        if len(self.available_tools) > 0:
            config['tools'] = []
            for tool_name, tool_func in self.available_tools.items():
                config['tools'].append(function_to_json(tool_func))
                
        if 'tools' in config:
            for tool in config['tools']:
                params = tool["function"]["parameters"]
                params["properties"].pop(__CTX_VARS_NAME__, None)
                if __CTX_VARS_NAME__ in params["required"]:
                    params["required"].remove(__CTX_VARS_NAME__)
        
        if self.result_type:
            config['response_format'] = {
                'type': 'json_object'
            }
        
        self.update_model_config(config)
        if self.verbose:
            print_config(self.name,self.model_config)

        if self.lifecycle:
            self.lifecycle.on_run_agent()
            
        # TODO 添加进度条 rich progresss
        @chat
        def result()->RecursionError:
            try:
                if self.is_debug:
                    with open(f'{self.name}.pkl', 'rb') as file:
                        response = pickle.load(file)
                else:
                    # pass
                    response = self.client.chat(self.model_config)
                    timestamp = time.time()
                    with open(f'{self.name}_{timestamp}.pkl', 'wb') as file:
                        pickle.dump(response,file)
                
                return ResponseOrError.from_response(response)
            except Exception as e:
                return ResponseOrError.from_error(e)


        if result.is_ok():
            if self.lifecycle:
                self.lifecycle.on_end_run_agent()
            response = result.unwrap()
            # TODO Generict[T] T 约束 
            # print(response)
            res:Result = self.ResultType(response=response,
                                 messages=self.messages,
                                 result_type=self.result_type)
            
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
                
            self.update_result(res)
            return res 
        else:
            if self.lifecycle:
                self.lifecycle.on_end_run_agent()
            error = result.error
            return ErrorResult(response=error)


    def __str__(self):
        return f"""
Hey I am {self.name}
Clent: {self.client.name}
{'-'*20}
system message: \n
{self.system_message}
{[ tool['function']['name'] for tool in self.available_tools ] if self.available_tools else "暂时没有提供任何工具"}
"""
    