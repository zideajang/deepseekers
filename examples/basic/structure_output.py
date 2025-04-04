import asyncio

from rich.console import Console
from rich.panel import Panel
from pydantic import BaseModel,Field
from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
from azent.core.utils import _json_schema_to_example

console = Console()

class Pizza(BaseModel):
    name:str = Field(title="name of pizza",description="披萨的名称",examples=["海鲜披萨"])
    description:str = Field(title="description of pizza",description="对于披萨的简单介绍",examples=["丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"])


system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="生成 10 种以上披萨")


agent = Agent(
    name="pizza_generator",
    model_name="deepseek-chat",
    system_message=system_message,
    result_data_type=list[Pizza]
    )

async def main():
    result = await agent.run(human_message)
    for pizza in result.get_data():
        console.print(Panel(pizza.description,title=f"🍕 {pizza.name}"))
    
if __name__ == "__main__":
    asyncio.run(main=main())