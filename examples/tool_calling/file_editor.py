import json

from typing import List,Union
from pydantic import BaseModel,Field

from deepseekers.core import Project,Agent,DeepSeekClient
from deepseekers.core.project import get_project
from deepseekers.client import OllamaClient
from deepseekers.result import OllamaResult
from deepseekers.core.message import ToolMessage,AIMessage
from deepseekers.core.project import Project,get_project
from deepseekers.core.utils import _json_schema_to_example,print_messages
from rich.console import Console

console = Console()

# 准备工具，在项目会用到的工具
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


# 任务 model，description 对于分解完子任务进行描述，任务用到工具
class Task(BaseModel):
    description:str = Field(title="description of task",description="对于任务的描述",examples=['读取文件'])
    tools:Union[List[str],str] = Field(default=[],title="tools of task",description="任务会用到工具，也可以没为空",examples=['read_file'])

# 任务列表，为 planAgent 也就是规划阶段输出的数据格式
class TaskList(BaseModel):
    task_list:List[Task] = Field(title="task list",description="任务列表，一些列任务",examples=[
        f"""[
{_json_schema_to_example(Task,is_flag=False)}
               ]"""
    ])

# 定义 single Agent
agent = Agent(
    name="deepseek-name",
    result_type=TaskList
    )
# TODO 支持绑定列表
agent.bind_tools([write_file,read_file])

# 定义一个项目
class FileSearchProject(Project):
    def setup(self):
        console.print("Setup ...")
    
    def clean(self):
        console.print("Project closing...")

file_manager_project = FileSearchProject(
    name="file_manager_project",
    description="对于给定文件进行操作，读取、编辑和写入",
    workspace_dir="./examples/tool_calling",
    tools=[read_file,write_file]
)

# 分解任务
@file_manager_project.step()
def decomposition(project:FileSearchProject):
    project_description = project.description
    tool_names = [ tool.__name__ for tool in project.tools]
    @agent.system_prompt()
    def file_manager_prompt_system(context,file_path):
        return f"""
AVAILABLE_TOOLS = {tool_names}
file_path:{file_path}
{_json_schema_to_example(TaskList)}
"""
    file_manager_prompt_system(file_path="./examples/tool_calling/demo.txt")

with get_project(proj=file_manager_project) as project:
    decomposition(project=project)
    result = agent.run(f"根据{project.description}，规划任务，将任务根据进行分解 2 - 3 子任务,对于<task> 将 file_path 文件中 deepSeeker 替换为 deepSeek <task>")
    agent.add_message(AIMessage(content=f"任务列表 {result.get_data().model_dump_json()}"))
    for task in result.get_data().task_list:
        result = agent.run(task.description)
        message = result.get_message()[0]
        if isinstance(message,ToolMessage):
            result = agent.available_tools[message.tool_name](**json.loads(message.tool_arguments))
            if isinstance(result,str):
                agent.add_message(AIMessage(content=result))
            else:
                print(result)
        else:
            agent.add_message(message=message)

    print_messages(messages=agent.messages)


