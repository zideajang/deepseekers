from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
from deepseekers.handoff import handoff_with_tool
from deepseekers.tool import result_process
from deepseekers.core.message import HumanMessage,SystemMessage,BaseMessage
from deepseekers.utils import run_agent_loop,EventManager,EventType,Span

console = Console()

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

# 准备 system message 和 human message 共同组成 prompt
system_message = SystemMessage(content="you are very help assistant")
js_system_message = SystemMessage(content="you are very javascript expert")
py_system_message = SystemMessage(content="you are very python expert")
human_message = HumanMessage(content="用 JavaScript 写一个生成随机数的函数")

# 初始化一个 JavaScript 专家智能体
js_agent = Agent(
    name="Js_Agent",
    system_message=js_system_message,
    )

# 初始化一个 Python 专家智能体
py_agent = Agent(
    name="Py_Agent",
    system_message=py_system_message
)

triage_agent = Agent(
    name="Triage_Agent",
    system_message=system_message,
    )

def on_handoff(agent_name):
    console.print(agent_name)

@handoff_with_tool(agent=js_agent,on_handoff=on_handoff)
def handoff_js_agent(input:str):
    """关于 JavaScript 方面编程问题可以转交给函数来完成
    """
    return input
event_manager = EventManager()
def on_message(message:BaseMessage):
    console.print(Panel(message.content,title="user"))
def on_response(message:BaseMessage):
    console.print(Panel(message.content,title="Assistant"))
    
event_manager.register_observer(EventType.OnMessage,on_message)
event_manager.register_observer(EventType.OnResponse,on_response)

triage_agent.bind_tool("handoff_js_agent",handoff_js_agent)
console.print(triage_agent.available_tools)
result = triage_agent.run(human_message)
result_process(triage_agent,result,event_manager,auto_call_agent=False)
# console.print(Markdown(result.get_text()))