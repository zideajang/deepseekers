import hashlib
import time
import pickle
import inspect



from typing import Dict,Any,Union,Optional,List,Callable
from functools import wraps
import inspect
from deepseekers.core import Client
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
def chat(f):
    return f()

class AgentDep:
    pass

__CTX_VARS_NAME__ = "context"

class Agent[D,T]:
    def __init__(self,
                 name:str,
                 client:Client,
                 model_name:str,
                 context:Optional[Union[Dict[str,Any],Callable[...,Dict[str,Any]]]]=None,
                #  TODO 以后 system message 增加支持模板类
                # 运行时可以动态传一些参数 system，systemplate.render()
                 system_message:Optional[Union[str,SystemMessage]] = None,
                
                 deps_type:Optional[type] = None,
                 result_type:Optional[type]= None,
                 
                 verbose:bool = True
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

        self.verbose = verbose
        self.model_name = model_name
        self.deps_type = deps_type
        self.deps = None
        # 共享上下文数据
        # TODO
        self.context = context
        if self.deps_type:
            if 'deps' not in self.context.keys():
                raise ValueError("需要在 context 提供 deps 字段内容")
            self.deps = self.context['deps']
            
        # TODO 以后还会进行进一步扩展 
        # - 可用工具 check tool_name 是不是可用，
        # - 该工具是否为授权工具，如果不是授权工具，执行需要用户确认
        self.available_tools:Dict[str,Callable] = {}
        self.result_type = result_type

        
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

    # @property
    # def system_prompt_content(self):
    #     if len(self.messages) > 0 and self.messages[0].role == MessageRole.System:
    #         return self.messages[0].content
    #     else:
    #         return ""
    
    def tool(self,func):
        self.bind_tool(func.__name__,func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            # self.available_tools[tool_name if tool_name else func.__name__] = func
            # TODO
            func(*args, **kwargs)
        return wrapper
    
    def tool_with_context(self,func):
        self.bind_tool(func.__name__,func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            # self.available_tools[tool_name if tool_name else func.__name__] = func
            # TODO
            func(self.context,*args, **kwargs)
        return wrapper
    
    def bind_tool(self,tool_name:str,func:Callable):
        # console.print("bind_tool")
        self.available_tools[tool_name if tool_name else func.__name__] = func

    def unbind_tool(self,func):
        self.available_tools.pop(func.__name__)
        # TODO 遍历 self.tools 中所有工具，删除目标对象
        if len(self.tools) == 1:
            self.tools = []
        elif len(self.tools) > 1:
            for i in range(len(self.tools)):
                if self.tools[i].name == func.__name__:
                    del self.tools[i]
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
                parameters = list(func_signature.parameters.keys())
                timestr = time.strftime("%Y%m%d-%H%M%S")
                prompt_id = hashlib.md5(func_code.encode()).hexdigest()
                pormpt_dict ={
                    "id":prompt_id,
                    "name":func_name,
                    "decription":func.__doc__,
                    "code":func_code,
                    "parameters": parameters,
                    "model_name":self.model_name,
                    "time":timestr
                }
                with open(f"./prompt_store_v2/{prompt_id}-{timestr}.pkl", "wb") as f:
                    pickle.dump(pormpt_dict, f)
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
        
        if deps:
            deps_value:D = deps.pop('deps', None)
            self.update_deps(deps_value)

        self.add_message(query)
        if self.deps:
            # deps_value
            # deps_type
            self.messages[-1].content += self.deps.model_dump_json()
        
        messsages = self.messages_to_dict()
        # 
        config = {
            "model":self.model_name,
            "messages":messsages,
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
            
        # TODO 添加进度条 rich progresss
        @chat
        def result()->RecursionError:
            try:
                response = self.client.chat(self.model_config)
                # console.print(response)
                return ResponseOrError.from_response(response)
            except Exception as e:
                return ResponseOrError.from_error(e)


        if result.is_ok():
            response = result.unwrap()
            # TODO Generict[T] T 约束 
            res = DeepseekResult(response=response,
                                 messages=self.messages,
                                 result_type=self.result_type)
            self.update_result(res)
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
{self.system_message}
{[ tool['function']['name'] for tool in self.tools ] if self.tools else "暂时没有提供任何工具"}
"""
    