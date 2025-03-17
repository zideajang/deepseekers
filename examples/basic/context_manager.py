
import json
from rich.console import Console
from rich.markdown import Markdown

from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.context_manager import DefaultContextManager
from deepseekers.core.message import HumanMessage,SystemMessage,ToolMessage
console = Console()


def my_callback(action, key, value):
    console.print(f"Action: {action}, Key: {key}, Value: {value}")

default_context = DefaultContextManager(my_callback)
# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="读取 ./examples/basic/hello.txt 文件的内容")



agent = Agent(
    name="deepseeker_001",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context=default_context
    )


@agent.tool_with_context
def read_file(context,file_path:str)->str:
    """读取文件内容
    """
    with open(file_path,'r',encoding='utf-8') as f:
        content = f.readlines()
    context['input'] = content
    return content

console.print(agent.available_tools)
result = agent.run(human_message)
message = result.get_message()[0]
if isinstance(message,ToolMessage):
    func_arguments = json.loads(message.tool_arguments)
    func_arguments['context'] = agent.context
    result = agent.available_tools[message.tool_name](**func_arguments)
    
# console.print(Markdown(result.get_text()))
