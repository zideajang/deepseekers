import os
import re
import sys

import tempfile
import subprocess
from typing import Callable,Dict,Any,Union,List
from functools import wraps

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

import pandas as pd
import inspect

from azent.core import DeepSeekClient, Agent
from azent.core.message import HumanMessage,BaseMessage,MessageRole,FileMessage,ErrorMessage,AIMessage
from azent.core import Result
from azent.core.run_context import RunContext
from azent.core.message import ErrorMessage, AIMessage,CodeMessage,ToolMessage
from azent.provider.csv_provider import CSVProviderContext
from azent.core.utils import function_to_json
from azent.provider import modify_function_schema
console = Console()

class ProviderResult(Result):
    def __init__(self,  messages):
        super().__init__(response=None)
        self.messages = messages
    def get_message(self):
        return self.messages
    def get_data(self):
        raise NotImplementedError()
    def get_text(self):
        raise NotImplementedError()

def run_temporary_python_code(self,python_code):
    """
    创建一个临时文件，写入 Python 代码，执行它，然后删除该文件。

    Args:
        python_code (str): 要执行的 Python 代码。
    """
    messages = []
    try:
        # 创建一个临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8',delete=False) as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(python_code)
            messages.append(FileMessage( content=f"Python 代码已写入临时文件: {tmp_file_path}"))

        # 执行临时文件
        process = subprocess.run([sys.executable, tmp_file_path], capture_output=True, text=True, check=True)
        messages.append(CodeMessage(content=f"\n执行结果:\n{process.stdout}"))
        if process.stderr:
            messages.append(ErrorMessage(content=f"\n错误信息:\n{process.stderr}"))

    except subprocess.CalledProcessError as e:
        messages.append(CodeMessage(content=f"\n执行临时文件出错 (返回码 {e.returncode}):\n{e.stderr}"))
    except FileNotFoundError:
        messages.append(ErrorMessage(content=f"\n错误: Python 解释器未找到。请确保 Python 已正确安装并添加到系统路径。"))
    except Exception as e:
        messages.append(ErrorMessage(content=f"\n发生其他错误: {e}"))
    finally:
        # 删除临时文件
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            messages.append(FileMessage(f"\n临时文件已删除: {tmp_file_path}"))

    return messages

def csv_provider_system_prompt(df):
    return f"""
你是一位精通 CSV 数据处理的 AI Agent。你的任务是将用户输入的任何自然语言描述或意图转换为可以直接操作 CSV 文件的指令或操作。

表格基本信息
### 基本统计信息
{df.describe()}
### 基本类型信息
{df.dtypes}
### 列信息
{df.columns}

1. **代码生成**：
- 如果用户需求涉及表格操作（如筛选、排序、计算等），生成对应的代码并放在 `<code>` 标签之间。
- 如果用户需求与表格操作无关，则无需生成代码，直接回复用户即可。

2. **输出格式**：
- 需要生成代码时：
    <code>
    {{代码}}
    </code>
- 无需生成代码时：
    直接回复用户，无需包含 `<code>` 标签。

3. **示例**：

**EXAMPLE 1**（需要生成代码）：
    - INPUT: 搜索 age 在 20 到 30 之间的数据
    - OUTPUT:
        <code>
        df[df['age'].between(20.0, 30.0)]
        </code>

**EXAMPLE 2**（无需生成代码）：
    - INPUT: 你好、你好呀，与表格操作无关
    - OUTPUT: 你好！请问有什么关于表格操作的问题吗？
            
**EXAMPLE 3**（需要生成代码）：
    - INPUT: 筛选出 salary 大于 50000 的数据
    - OUTPUT:
        <code>
        df[df['salary'] > 50000]
        </code>
            
**EXAMPLE 4**（需要生成代码）：
    - INPUT: 列出表格列名
    - OUTPUT:
        <code>
        df.columns
        </code>
**EXAMPLE 5**（需要生成代码）：
    - INPUT:  按 age 列升序排序
    - OUTPUT:
        <code>
        df.sort_values(by='age', ascending=True)
        </code>

**EXAMPLE 6**（无需生成代码）：
- INPUT: 你好，今天天气怎么样？
- OUTPUT: 你好！请问有什么关于表格操作的问题吗？

4. **任务**：
根据用户输入，判断是否需要生成代码，并按规则输出。
"""

def run_temporary_python_code(python_code):
    """
    创建一个临时文件，写入 Python 代码，执行它，然后删除该文件。

    Args:
        python_code (str): 要执行的 Python 代码。
    """
    messages = []
    try:
        # 创建一个临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',dir="./temp",delete=False,encoding="utf-8") as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(python_code)
            messages.append(FileMessage(content=f"Python 代码已写入临时文件: {tmp_file_path}"))

        # 执行临时文件
        process = subprocess.run([sys.executable, tmp_file_path], capture_output=True, text=True, check=True)
        messages.append(CodeMessage(content=f"\n执行结果:\n{process.stdout}"))
        if process.stderr:
            messages.append(ErrorMessage(content=f"\n错误信息:\n{process.stderr}"))

    except subprocess.CalledProcessError as e:
        messages.append(ErrorMessage(content=f"\n执行临时文件出错 (返回码 {e.returncode}):\n{e.stderr}"))
    except FileNotFoundError:
        messages.append(ErrorMessage(content=f"\n错误: Python 解释器未找到。请确保 Python 已正确安装并添加到系统路径。"))
    except Exception as e:
        messages.append(ErrorMessage(content=f"\n发生其他错误: {e}"))
    finally:
        # 删除临时文件
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            messages.append(FileMessage(content=f"\n临时文件已删除: {tmp_file_path}"))

    return messages


class CSVProvider:
    def __init__(self,
                 name:str):

        self.name = name
        self._version = "1.0.0"
        self._context:List[CSVProviderContext] = []
        self._action_dict: Dict[str, Callable] = {}
        self._tools = []
    def resource(self,name:str):
        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                result = func(*args, **kwargs)
                self._context.append(result)
                return result
            return inner
        return wrapper
    
    @property
    def tools(self):
        return self._tools
    
    def tool(self,name:str,description:str=None,parameters: Dict[str, str] = None):
        def wrapper(func):
            if name in self._action_dict:
                raise ValueError(f"Tool with name '{name}' already registered.")
            signature = inspect.signature(func)
            expected_parameters = list(signature.parameters.keys())
            self._action_dict[name] = {
                "function": func,
                "description": description,
                "parameters": parameters if parameters is not None else {param: "" for param in expected_parameters},
                "expected_parameters": expected_parameters,
            }
            func_json_schema = modify_function_schema(function_to_json(func))
            self._tools.append(func_json_schema)
            @wraps(func)
            def inner(*args, **kwargs):
                result = func(*args, **kwargs)
                return result
            return inner
        return wrapper


    @property
    def data(self):
        return [ item.data for item in self._context]
    
    def get_data(self,name:str):
        if name in self._data:
            return self._data[name]
        else:
            raise ValueError(f"没有找到 {name}")
        
    def extract_command(self,result:Result):
        if isinstance(result.get_message()[0],ToolMessage):
            tool_message:ToolMessage = result.get_message()[0]
            try:
                arguments_dict = eval(tool_message.tool_arguments)
                return {
                    "action": "invoke_tool",
                    "tool_name": tool_message.tool_name,
                    "parameters": arguments_dict
                }
                    
            except (SyntaxError, NameError, TypeError):
                print(f"Warning: Could not safely evaluate tool_arguments: {tool_message.tool_arguments}")
                return None
        return None
    def run_command(self,commond):
        ...

class CodePrompt[T]:
    def get_system_prompt(self,prompt:Callable):
        ...

    def parser(self,result:T):
        pass    

class CSVAgent:
    def __init__(self, 
                 name:str, 
                 system_prompt:str|Callable, 
                 csv_path:str|pd.DataFrame, 
                 agent:Agent|None = None,
                 delimiter=',', has_header=True):
        self.name = name
        # 初始化一个 Provider
        self.provider = CSVProvider(name, csv_path, delimiter, has_header)
        # TODO 
        self._df = self.provider.data
        # 
        system_prompt = system_prompt or csv_provider_system_prompt(self._df)

        # 初始化 
        if agent:
            self.agent = agent
        else:
            self.client = DeepSeekClient(name="deepseek-client")
            self.agent = Agent(
                name="csv_agent",
                system_message=system_prompt,
            )

    def get_data(self):
        return self._df

    def extract_code(self,result:Result)->BaseMessage:

        content = result.get_message()[0].content
        # TODO 这里正则是和 syste prompt 息息相关，所以这里需要优化，Prompt 
        match = re.search(r"<code>(.*?)</code>", content, re.DOTALL)
        
        if match:
            code_message = CodeMessage(content=match.group(1).strip(),lang='python')
            return code_message
        else:
            error_message = ErrorMessage(content="没有找到匹配的代码,")
            return error_message

    async def run(self,
                  query: Union[str, HumanMessage],
                  run_context: RunContext | None = None) -> Result:

        agent_result = await self.agent.run(query, run_context)
        message = self.extract_code(agent_result)
        result = ProviderResult(messages=[message])

        return result
    
    def sync_run(self,
                  query: Union[str, HumanMessage],
                  run_context: RunContext | None = None) -> Result:

        agent_result = self.agent.sync_run(query, run_context)
        
        # TODO 需要优化 prompt.parser(result)->List[BaseMessage]
        message = self.extract_code(agent_result)

        # TODO 作为一个通用组件
        messages = run_temporary_python_code(message.content)

        # messages.insert(0,message)
        result = ProviderResult(messages=[HumanMessage(content=query),message])

        return result


