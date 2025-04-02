import re
import json
import inspect
import hanlp

from typing import List, get_type_hints

from pydantic import BaseModel,Field
from deepseekers.core.message import BaseMessage
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def _json_schema_to_example( result_data_type:type,is_flag:bool=True):
    # TODO 待优化
    schema = result_data_type.schema()
    if not hasattr(result_data_type,'model_json_schema'):
        raise TypeError("现在仅支持继承 BaseModel 的类")
    if is_flag:
        res = ""
        for field_name, field_info in schema["properties"].items():
            res += f"""
字段名称：{field_name}, 描述：{field_info.get('description')}
"""
        res += """
EXAMPLE JSON OUTPUT\n"""

    else:
        res = ""
    json_schema = result_data_type.model_json_schema()
    if 'properties' in  json_schema:
        example = {}
        for k,v in json_schema['properties'].items():
             example[k] = v['examples'][0]
        res += f"""
{example}
"""
    return res

def is_snake_case(s):
    """
    检查字符串是否符合 snake_case 命名规范。
    :param s: 要检查的字符串
    :return: 如果符合规范返回 True，否则返回 False
    """
    # 正则表达式规则
    pattern = r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
    return bool(re.match(pattern, s))


def is_markdown(text):
    """
    判断文本是否为 Markdown 格式。

    Args:
        text: 要判断的文本字符串。

    Returns:
        如果文本是 Markdown 格式，则返回 True，否则返回 False。
    """

    # 简单的 Markdown 语法检查
    markdown_patterns = [
        r'^#+\s',  # 标题
        r'^\*|\-|\+\s',  # 列表
        r'\[(.*?)\]\((.*?)\)',  # 链接
        r'\*\*(.*?)\*\*',  # 粗体
        r'\*(.*?)\*',  # 斜体
        r'`(.*?)`', # 代码块
        r'>\s', # 引用
        r'^\d+\.\s' #有序列表
    ]

    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True

    return False

def print_message_role(message_role):
    if message_role == 'user':
        return f"🧑 {message_role}"
    elif message_role == 'assistant':
        return f"🤖 {message_role}"
    return message_role

def print_config(name,config):
    markdown_content = ""
    if 'model' in config:
        markdown_content += f"""
## model
{config['model']}
## messages:
""" 
    if 'messages' in config:
        for message in config['messages']:
            markdown_content += f"""
{print_message_role(message['role'])}
{message['content']}

"""
    console.print(Panel(Markdown(markdown_content),title=name),style="green bold")

def print_message(message:BaseMessage):
    # TODO
    if isinstance(message.content, str):
        if is_markdown(message.content):
            console.print(Panel(Markdown(message.content),title=message.role))
        else:
            console.print(Panel(message.content,title=message.role))
    else:
        console.print(Panel(str(message.content),title=message.role))
    

def print_messages(messages:List[BaseMessage]):
    for message in messages:
        print_message(message)
        



def get_type_name(t):
    name = str(t)
    if "list" in name or "dict" in name:
        return name
    else:
        return t.__name__
    
def function_to_json(func):
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
