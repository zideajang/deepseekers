
import json
from typing import Protocol
from rich.console import Console
from rich.markdown import Markdown

from azent.core import DeepSeekClient,Agent
from azent.core.agent import AgentLifeCycle,AgentLifeCycleInterface
from azent.core.context_manager import DefaultContextManager
from azent.core.message import HumanMessage,SystemMessage,ToolMessage
from azent.core.task import create_task,TaskInterface
from azent.core.utils import _json_schema_to_example,print_config,function_to_json

console = Console()


def my_callback(action, key, value):
    console.print(f"Action: {action}, Key: {key}, Value: {value}")

default_context = DefaultContextManager(my_callback)
# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="读取 ./examples/basic/hello.txt 文件的内容")

class SimpleAgentLifeCycle(AgentLifeCycle):
    def __init__(self, agent:Agent):
        super().__init__(agent)
    def on_bind_tool(self,agent_name,tool_name):
        console.print(f"{agent_name}{tool_name}")

    def on_tool_call(self,tool_name,tool_arguments):
        console.print(f"{tool_name}{tool_arguments}")

    def on_end_tool_call(self,tool_name,tool_arguments,result):
        console.print(f"{tool_name}{tool_arguments}\n,{result}")
    def on_run_agent(self):
        print_config(self.agent.name,self.agent.model_config)

    def on_end_run_agent(self):
        console.print("on_end_run_agent")

agent = Agent(
    name="deepseeker_001",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context={},
    verbose=False
    )
simple_lifecycle = SimpleAgentLifeCycle(agent)
def read_file(file_path:str)->str:
    """读取文件内容
    """
    with open(file_path,'r',encoding='utf-8') as f:
        content = f.readlines()
    return content

    
class Task:

    def __init__(self,name:str,agent:Agent,cb:AgentLifeCycleInterface):
        self.name = name
        self.agent = agent
        self.cb = cb

    def setup(self):
        self.agent.bind_tool("read_file",read_file)
    
    def start(self,query:str):
        result = self.agent.run(query)
        result = agent.run(human_message)
        message = result.get_message()[0]
        if isinstance(message,ToolMessage):
            self.cb.on_tool_call(message.tool_name,message.tool_arguments)
            func_arguments = json.loads(message.tool_arguments)
            result = agent.available_tools[message.tool_name](**func_arguments)
            self.cb.on_end_tool_call(message.tool_name,message.tool_arguments,result)
            
    def end(self):
        console.print(f"{self.name} 任务结束")

task = Task("simple_task",agent,simple_lifecycle)

with create_task(task,default_context) as context:
    task.start("读取 ./examples/basic/hello.txt 文件的内容")





    
# console.print(Markdown(result.get_text()))
