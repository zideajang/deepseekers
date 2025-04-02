import asyncio

from rich.console import Console
from rich.markdown import Markdown

from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
console = Console()

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="write hello world in python")


agent = Agent(
    name="simple_agent",
    system_message=system_message,
    )

async def main():
    result = await agent.run(human_message)
    if result:
        console.print(result.get_text())
if __name__ == "__main__":
    asyncio.run(main=main())