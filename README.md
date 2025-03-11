# deepseekers(标准版)

![图片描述](images/bannar.jpg)

轻量级多 Agent 协作 AI Agent 框架(标准版)

初始化 client 在项目中，提供了对于 deepseek API 的封装方便大家快速接入 deepseek 模型

## example
## 😀 hello 第一行代码
\examples\basic\hello.py
```python
from rich.console import Console
from rich.markdown import Markdown

from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
console = Console()

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

# 准备系统消息(SystemMessage)和用户消息(HumanMessage)
system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="write hello world in python")

# 初始化一个 🤖 
agent = Agent(
    name="deepseeker_001",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context={}
    )
# 运行 Agent 💻
result = agent.run(human_message)
console.print(Markdown(result.get_text()))
```

## 结构化输出 🍕
结构化输出，轻松接入到现有系统
```python

from rich.console import Console
from rich.markdown import Markdown
from typing import List
from pydantic import BaseModel,Field
from rich.panel import Panel
from deepseekers.core import DeepSeekClient,Agent
from deepseekers.core.message import HumanMessage,SystemMessage
from deepseekers.core.utils import _json_schema_to_example

console = Console()
# 定义数据数据结构，现在仅支持 BaseModel 类型
# 并且需要给出例子，📢这一点比较重要
class Pizza(BaseModel):
    name:str = Field(title="name of pizza",description="披萨的名称",examples=["海鲜披萨"])
    description:str = Field(title="description of pizza",description="对于披萨的简单介绍",examples=["丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"])

class PizzaList(BaseModel):
    pizza_list:List[Pizza] = Field(title="pizza list",description="给出一个披萨列表",examples=[f"""
{_json_schema_to_example(Pizza)}
"""])

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="生成 10 种以上披萨")


agent = Agent(
    name="pizza_generator",
    model_name="deepseek-chat",
    system_message=system_message,
    client=client,
    context={},
    # 📢  需要在初始化 Agent 时候指定一些输出数据结构
    result_type=PizzaList
    )

result = agent.run(human_message)
for pizza in result.get_data().pizza_list:
    console.print(Panel(pizza.description,title=f"🍕 {pizza.name}"))
    
```