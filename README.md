# 🚀 deepseekers(标准版)

## deepseekers 是个啥
轻量级多 Agent 协作的 AI Agent 框架(标准版)

## deepseekers 的目标人群是谁

会专注于几个适合引入 AI 的领域、例如翻译协作、数据分析、辅助开发。专注几个领域深挖，收集问题形成针对这些领域的解决方案。通过Agent增强LLM稳定性、可控性，从而提升 Agent 价值。

## 应用场景
- 📰 翻译协作
- 📊 数据分析
- ☕️ 辅助开发

## 特点
- 面向落地，每一行代码都是为了 AI 能够触地而写
- 不做通用，通过不断实践来探究 AI 领域的特定领域的落脚点，通过对于业务深入了解，通过先验来减少不必要问题
- 通过机器学习加持，压缩 LLM 自由度
- 无感切入，希望无需任何成本，就可以将 LLM 引入到现有系统，甚至渗透到函数这一个基础的单元
- 对于 **标准版** 希望他不仅仅是一个 Agent 框架，而是一版教你如何写自己 Agent 的过程书，每一次提交都可能是一个 python 的语法，都是一个解决方案，一个特征
- 他是变化的，不过引入新的特征，以便于适应当先 LLM 快速的迭代
- 最小集，希望在不断跟随 LLM 过程让版本切换成本达到最小

## 示例

## 😀 hello 第一行代码
### 准备
如何想要接入 deepseek 模型，需要准备 api_key
- 打开 deepseek 官网
- 注册一个 deepseek 账号
- 接下来申请 api_key 作为 DEEPSEEK_API_KEY 
😀 注意要把账号保存好呀

### 初始化 client 🎉
一切从 Hello world 开始，你的 deepseeker ✈️ 之旅也是从 Hello 例子开始。首先初始化一个 client ，client 对应一个 LLM 供应商，或者对应本地起的 LLM 服务，例如 ollama。个人这里并不推荐使用。

```python
client =  DeepSeekClient(
        name="deepseek-client",
        api_key = DEEPSEEK_API_KEY,
        base_url = DEEPSEEK_BASE_URL)
```
需要准备一个 api_key deepseek 关注注册一个账号，因为是需要 api_key 


### 📝 准备系统消息(SystemMessage)和用户消息(HumanMessage)
```python
system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="write hello world in python")
```
这里 system_message 设计比较灵活，可以通过多种方式创建 system_message，在后面例子大家就能看到更多方式来定义 system_message

### 定义一个 🤖 Agent
```python
agent = Agent(
    name="simple_agent",
    system_message=system_message,
    )
```
简简单单的配置就可以完成 Agent 初始化。在 Agent 设计时，借鉴了很多框架中 Agent 模样，具体 Agent 应该长什么样呢? 最后的设计是想让开发人员只要较少的参数。就可以创建出来一个 Agent，而且还能够满足 Agent 基本能力。所以这是现在大家看到 Agent 模样，一些基本的参数就可以创建出一个 Agent。

一切准备好了，就可以开始运行 Agent 了，这里要补充一点，在 deepseekers 框架设计中，一切都是优先考虑支持异步调用，为什么这样做，原因也是不必多说了。


```python
async def main():
    result = await agent.run(human_message)
    if result:
        console.print(result.get_text())
if __name__ == "__main__":
    asyncio.run(main=main())
```
完整代码如下
```python
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
```

当然通常也支持同步方式来运行 Agent，具体方法如下

```python

if __name__ == "__main__":
    result = agent.sync_run(human_message)
    if result:
        console.print(result.get_text())
```


### demo 2 满足结构化输出，生成 🍕 数据

## 结构化输出重要性

**结构化输出**是指 LLM 生成的结果，按预定义的格式或模式来输出，例如 JSON、XML、表格、列表等。这种能力对于 LLM 在实际应用中至关重要，原因如下：

- 兼容现有系统
- 提升可控性
- 通向多多模态的接口。

简化后续处理: 将 LLM 的输出结构化为 Pydantic 模型后，Agent 可以直接访问和操作这些数据，而无需进行额外的文本解析工作，从而简化了后续的逻辑处理。

结构化输出，轻松接入到现有系统，我觉得结构化输出和工具调用是现代 LLM 必备的两种技能，如果还没有这 2 个技能就很难混了。接下来就通过生成 🍕 数据为演示通过 Agent 让你可以省力让 deepseek 给出结构化输出，和上一个例子重复就不再重复了。


首先是定义数据结构，这是一个嵌套数据结构，Pizza 🍕 和一个 Pizza 🍕🍕🍕列表的数据。

📢 **提示**: 结构化输出这里在 `v2` 版本也做一定的优化，就是返回类型集合情况，不再需要定义该类型集合类来接受输出结构，可以通过 `list[Pizza]` 来告诉 Agent 返回的类型为 `Pizza` 的集合类型。

🚨 **注意**: 这里指定返回结构化的数据类型修改为 用 `result_data_type` 来指定，而不再是 `result_type` 。这里 `result_type` 具有新的含义，表示 `agent.run` 或者 `agent.sync_run` 返回结构类型。所以进行这样修改就是为了可以通过参数名字可以准确表达参数用途。

例如
```python
class PizzaList(BaseModel):
    pizza_list:List[Pizza] = Field(title="pizza list",description="给出一个披萨列表",examples=[f"""
{_json_schema_to_example(Pizza)}
"""])
```
例如无需再去指定 `PizzaList` 作为 `Pizza` 集合类的类型，直接指定 `list[Pizza]` 即可

```python
class Pizza(BaseModel):
    name:str = Field(title="name of pizza",description="披萨的名称",examples=["海鲜披萨"])
    description:str = Field(title="description of pizza",description="对于披萨的简单介绍",examples=["丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"])

class PizzaList(BaseModel):
    pizza_list:List[Pizza] = Field(title="pizza list",description="给出一个披萨列表",examples=[f"""
{_json_schema_to_example(Pizza)}
"""])
```
**提示**: 📢 暂时只支持 pydantic 的 BaseModel 类型的数据，如果又其他类型，可以将其转换为 pydantic 类型

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



system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="生成 10 种以上披萨")

# 定义一个 Agent
agent = Agent(
    name="pizza_generator",
    model_name="deepseek-chat",
    system_message=system_message,
    # 📢  需要在初始化 Agent 时候指定一些输出数据结构
    result_type=list[Pizza]
    )

async def main():
    result = await agent.run(human_message)
    for pizza in result.get_data():
        console.print(Panel(pizza.description,title=f"🍕 {pizza.name}"))
    
if __name__ == "__main__":
    asyncio.run(main=main())
    
```

你提到的这两种方案都是在 LLM 本身不直接支持或难以保证完全结构化输出时，将非结构化或半结构化输出转化为结构化数据的有效方法。我们来分别探讨一下这两种方案的细节和适用场景。

方案一：Prompt 引导 JSON 输出 + json_extract + Pydantic 模型

这种方案的核心思想是引导 LLM 尽量输出 JSON 格式的数据，即使它本身不具备强结构化输出的能力，然后通过后处理的方式提取和校验 JSON 数据，并最终转换为 Pydantic 模型。

方案二：使用支持结构化输出的 Agent 分析和提取

这种方案利用了 Agent 框架（如 LangChain、AutoGen 等）中具备更强逻辑和工具调用能力的 Agent，来分析 LLM 的原始输出，并根据预定义的结构提取所需的信息。

### 通过 deps 来首先动态获取资源

有时候会有这样的场景，我们需要发起请求时候获取一些资源作为 LLM 请求时候的背景知识。这时候需要依赖，这种依赖可能是网络资源、数据库资源和文件系统。


### 定义依赖数据结构
```python
@dataclass
class MyDeps:  
    http_client: httpx.Client
    url:str = "http://127.0.0.1:8000/pizzas"
```

然后将 system message 用一个函数包裹起来，函数形成欢迎，因为只有函数在执行才会确定，不然函数通过参数传入一些不确定因素，这个 Deps 只要运行 Agent 时候，执行 system_message 才会在运行获取数据。

```python
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
```

```python
result = agent.run(human_message,{'deps':deps})
```

```python
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


# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")

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
    
```