import json
from typing import List,Union
import httpx
from dataclasses import dataclass
from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
from deepseekers.core.utils import _json_schema_to_example

from pydantic import BaseModel,Field
from rich.console import Console
console = Console()

@dataclass
class MyDeps:  
    http_client: httpx.Client
    url:str = "http://127.0.0.1:8000/pizzas"



def system_message(deps:MyDeps)->SystemMessage:
    response = deps.http_client.get(deps.url)
    if response.status_code == 200:
        pizza_list = response.json()
    
        return SystemMessage(content=f"""
Pizzas
{json.dumps(pizza_list)}
""")
    else:
        console.print_exception(f"请求失败，状态码：{response.status_code}")
        console.print(response.text)
        return SystemMessage(content="")



class Pizza(BaseModel):
    name:str = Field(title="name of pizza",description="披萨的名称",examples=["海鲜披萨"])
    description:str = Field(title="description of pizza",description="对于披萨的简单介绍",examples=["丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"])

class PizzaList(BaseModel):
    pizza_list:List[Pizza] = Field(title="pizza list",description="给出一个披萨列表",examples=[f"""
{_json_schema_to_example(Pizza)}
"""])

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

# system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="从 Pizzas 数据筛选配料中有蘑菇的披萨")


agent = Agent(
    name="pizza_generator",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context={},
    )

with httpx.Client() as client:
    deps = MyDeps(http_client=client)
    result = agent.run(human_message,{'deps':deps})
    print(result.get_text())
    # for pizza in result.get_data().pizza_list:
    #     console.print(f"{pizza.name}")
    
# @agent.system_prompt  
# async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
#     response = await ctx.deps.http_client.get(  
#         'https://example.com',
#         headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  
#     )
#     response.raise_for_status()
#     return f'Prompt: {response.text}
# result = agent.run(human_message)
# for pizza in result.get_data().pizza_list:
#     console.print(Panel(pizza.description,title=f"🍕 {pizza.name}"))
    