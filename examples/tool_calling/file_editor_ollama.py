# 读取文件

# 全局替换
# 条件替换
# 保存文件

from azent.core import Project,Agent
from azent.core.project import get_project
from azent.client import OllamaClient
from azent.result import OllamaResult
from azent.core.message import ToolMessage


def read_file(file_path: str) -> str:
    """从指定路径读取文件内容。
    Args:
        file_path: 文件路径。
    Returns:
        文件内容（字符串），如果文件不存在或读取失败，则返回空字符串。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"文件未找到：{file_path}")
        return ""
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return ""
def write_file(file_path: str, file_content: str) -> bool:
    """将内容写入指定路径的文件。
    Args:
        file_path: 文件路径。
        file_content: 要写入的文件内容。
    Returns:
        写入成功返回 True，失败返回 False。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return True
    except Exception as e:
        print(f"写入文件时发生错误：{e}")
        return False

class OllamaAgent(Agent):
    def __init__(self, name, client = ..., model_name = 'deepseek-chat', context = None, system_message = None, deps_type = None, result_type = None, verbose = True):
        super().__init__(name, client, model_name, context, system_message, deps_type, result_type, verbose)
        self.ResultType = OllamaResult
    
file_manager_agent = OllamaAgent(
    name="ollama_agent",
    model_name="qwen2.5:latest",
    client=OllamaClient(name="ollama_client"),
    )

# TODO 支持绑定列表
file_manager_agent.bind_tool(write_file.__name__, write_file)
file_manager_agent.bind_tool(read_file.__name__,read_file)

@file_manager_agent.system_prompt()
def file_manager_prompt_system(context,file_path):
    return f"""
file_path:{file_path}
    """
file_manager_prompt_system(file_path="./examples/tool_calling/demo.txt")
# print(file_manager_agent.available_tools)
# print(file_manager_agent.system_message)
result = file_manager_agent.run("将文件中 deepSeeker 替换为 deepSeek")
for message in result.get_message():
    if isinstance(message,ToolMessage):
        print(message.tool_name)
        print(message.tool_arguments)
        result = file_manager_agent.available_tools[message.tool_name](**message.tool_arguments)
        # print(result)
        file_manager_agent.update_system_message(f"""
替换文件内容 
<file-content>
{result}
</file-content>
""")
        file_manager_agent.add_message({'role': 'tool', 'content': str(result), 'name': message.tool_name})
        import time
        time.sleep(30)
        print('call again')
        file_manager_agent.unbind_tool(read_file)
        file_manager_agent.unbind_tool(write_file)
        
        replace_result = file_manager_agent.run("将文件中 deepSeeker 替换为 deepSeek <file_content>替换后的内容</file_content>")
        print(replace_result.get_text())
        # messages.append()
        # MCP
