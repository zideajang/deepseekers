from rich.console import Console
from rich.markdown import Markdown

from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
console = Console()

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="write hello world in python")

# console.print(human_message.model_dump())

agent = Agent(
    name="deepseeker_001",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context={}
    )

result = agent.run(human_message)
console.print(Markdown(result.get_text()))
