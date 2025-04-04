# 🚀 aZent(标准版)

## aZent 是个啥
轻量级多 Agent 协作的 AI Agent 框架(标准版)

## aZent 的目标人群是谁

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

一切准备好了，就可以开始运行 Agent 了，这里要补充一点，在 azent 框架设计中，一切都是优先考虑支持异步调用，为什么这样做，原因也是不必多说了。


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

from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
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
from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
from azent.core.utils import _json_schema_to_example

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

## 😀 关于 deps 示例

有时候会有这样的场景，通常需要获取外部资源，这里外部可以是通过 http 请求获取资源，或者我们连接数据库来获取资源，也能读取本地文件。将这些资源整合到 context，例如我们需要阅读邮件，需要通过邮件接口来获取邮件内容。

这些资源都是外部，而且动态的，都是实时获取资源。所以启动 Agent 之前需要去连接资源，接通资源。这就是 deps 设计的目的。



### 定义依赖数据结构
```python
@dataclass
class Deps:
    conn:httpx.AsyncClient
    url:str
```
- 定义 Deps 数据用于连接服务API的客户端
- url 


```python
async def system_message(context):
    conn = context['deps'].conn
    try:
        response = await conn.get(context['deps'].url)
        response.raise_for_status()
        if response.status_code == 200:
            pokemon_list = [ Pokemon(name=item['name'],description="") for item in response.json()['results']]
            return f"""
        基于 **Pokemon** 出现的 Pokemon 给与简单说明，就一句话
        ** Pokemon **
        {",".join([ pokemon.name for pokemon in pokemon_list])}

        """
        else:
            return f"请求失败，状态码:{response.status_code}"
    except httpx.RequestError as exc:
        return f"{exc.request.url!r} 请求时出现错误"
    except httpx.HTTPStatusError as exc:
        return f"当发起 {exc.request.url!r} 请求，返回的状态码为 {exc.response.status_code} "
```

- 在 `system_prompt` 函数通过 `run_context` 来获取到 Deps 也就是拿到连接服务的客户端
- `system_prompt` 通过客户端发起请求拿到数据作为 context 一部分


然后将 system message 用一个函数包裹起来，函数形成欢迎，因为只有函数在执行才会确定，不然函数通过参数传入一些不确定因素，这个 Deps 只要运行 Agent 时候，执行 system_message 才会在运行获取数据。


```python
agent = Agent(
    name="deps",
    result_data_type=list[Pokemon]
    )
```

```python
async def main():
    async with httpx.AsyncClient() as client:
        dep = Deps(conn=client,url="https://pokeapi.co/api/v2/pokemon?limit=5")
        
        result = await agent.run("给出每一个 pokemon 的解释说明",run_context=RunContext(deps=dep))
        print(result.get_data())

if __name__ == "__main__":
    asyncio.run(main=main())
```
- 获取一个客户端(client)
- 初始依赖 Deps 在类中持有客户端的连接以及url
- 在 system_prompt 函数通过 run_context 来获取到 Deps 也就是拿到连接服务的客户端
- system_prompt 通过客户端发起请求拿到数据作为 context 一部分


```python
import asyncio
import httpx
from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel,Field

from azent.core import DeepSeekClient,Agent
from azent.core.run_context import RunContext

url = "https://pokeapi.co/api/v2/pokemon?limit=10"

client = DeepSeekClient(name="deepseek-client")

class Pokemon(BaseModel):
    name:str = Field(title="pokemon name",examples=['Charizard'])
    description:Optional[str] = Field(title="description of pokemon",description="",examples=["是《宝可梦》系列中的火系飞行系双属性宝可梦，外形像橙色巨龙，喷火能力强，是初代御三家小火龙的最终进化形态。"],default="")

# 依赖数据结构，通常是获取数据的前提，也就是连接网络和连接数据库
@dataclass
class Deps:
    conn:httpx.AsyncClient
    url:str
# system_message 通过 context 获取获取 dep 值
async def system_message(context):
    conn = context['deps'].conn
    response = await conn.get(context['deps'].url)
    # print(response.json()['results'])
    pokemon_list = [ Pokemon(name=item['name'],description="") for item in response.json()['results']]
    
    return f"""
基于 **Pokemon** 出现的 Pokemon 给与简单说明，就一句话
** Pokemon **
{",".join([ pokemon.name for pokemon in pokemon_list])}

"""
# 初始化 Agent 时候我们需要指定 Deps
agent = Agent(
    name="deps",
    result_data_type=list[Pokemon]
    )

async def main():
    async with httpx.AsyncClient() as client:
        
        dep = Deps(conn=client,url="https://pokeapi.co/api/v2/pokemon?limit=5")
        
        result = await agent.run("给出每一个 pokemon 的解释说明",run_context=RunContext(deps=dep))
        print(result.get_data())

if __name__ == "__main__":
    asyncio.run(main=main())
    
```

## 工具调用
函数是其他模块的基础，可以看作 AI Agent 框架核心中的核心，所以这个模块设计好坏会直接影响到使用你整个 AI Agent 框架的体验。

在 azent 中，支持将异步函数和同步函数作为工具提供给大语言模型。
### 同步函数的调用
#### 准备工具⚙️
所谓工具也就是函数，或者类可能是一个接口。为了让一个函数成为工具，我们是要做额外工作。准备工作主要是为函数的参数指定类型，对于返回值也是需要指定类型的，并且要给出符合 python 格式的 doc 说明，为什么要这么做，一切准备工作都是为了让语言模型更好地了解工具，以便在合适的时候选择一个工具来使用。
```python
def get_weather(location:str)->float:
    """获取某个城市天气的温度
    Args:
        location(str): 城市名称
    Returns:
        返回某个城市天气的温度
    """
    print(f"{location=}")
    return 22.0
```
注册函数方式可以显式的，也可以隐式注册
```python
agent.bind_tool("get_weather",get_weather)
```
也可以通过 `@agent.tool` 这样注解方式来将函数绑定到语言模型
```python
@agent.tool
def get_weather(location:str)->float:

    """获取某个城市天气的温度
    Args:
        location(str): 城市名称
    Returns:
        返回某个城市天气的温度
    """
    print(f"{location=}")
    return 22.0
```

这里做了一些优化，通过 `ToolManager` 类将对于工具管理从 Agent 移出来，通过一个外接工具管理器来注册工具以及管理工具。也就是减轻了 Agent 的负担。所以 `tool_manager` 负责对于工具管理，Agent 也是通过 bind_tool 将工具添加到 `tool_manager` 。


```python
async def main():
    result = await agent.run(human_message)

    for tool_message in result.get_message():
        tool_call_result = await agent.tool_manager.execute_tool(tool_message)
        console.print(tool_call_result.output)

if __name__ == "__main__":
    asyncio.run(main=main())
```

- 在 tool_manager 提供 `execute_tool` 用于执行函数

### 异步函数调用

```python

async def get_weather(location:str)->float:

    """获取某个城市天气的温度
    Args:
        location(str): 城市名称
    Returns:
        返回某个城市天气的温度
    """

    print(f"{location=}")
    await asyncio.sleep(2) 
    return 22.0
```
对于异步函数的绑定，除了要给函数名称，以及要绑定函数外，还需要给一个 `is_async = True`

```python
agent.bind_tool("get_weather",get_weather,is_async=True)
```

```python
async def main():

    result = await agent.run(human_message)
    console.print(result.get_message()[0])
    tool_call_result = await agent.tool_manager.execute_tool(result.get_message()[0])
    console.print(tool_call_result.output)
```
### 也支持 context 这样绑定
```python
@agent.tool
def get_weather(context,location:str)->float:

    """获取某个城市天气的温度
    Args:
        location(str): 城市名称
    Returns:
        返回某个城市天气的温度
    """
    # TODO
    print(context['deps']['name'])
    print(f"{location=}")
    return 22.0
```
也可以准备这样的工具，也就是第一个参数是 context, 这样工具在添加工具会过滤掉 context 这个参数。因为这个参数属于 Agent 内部上下文参数，而在 Agent 选择了第一个参数是 context 的工具，Agent 会自动补全这个参数。通常我们会将运行时 context。

## 任务扭转

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
from azent.handoff import handoff_with_tool
from azent.tool import result_process
from azent.core.message import HumanMessage,SystemMessage,BaseMessage
from azent.context_manager.default_event_manager import DefaultEventManager
from azent.context_manager import EventType
from azent.utils import run_agent_loop
console = Console()
```

```python

# 初始化一个 client
client = DeepSeekClient(name="deepseek-client")
```

```python
# 准备 system message 和 human message 共同组成 prompt
system_message = SystemMessage(content="""
当收到用户的请求时，请仔细阅读并思考这个请求最适合由哪个助手来处理。

如果用户的请求涉及到以下方面，请分配给 JavaScript 专家：
- 网页前端开发 (HTML, CSS, JavaScript)
- 浏览器行为和 DOM 操作
- JavaScript 框架和库 (如 React, Angular, Vue.js)
- Node.js 后端开发
- 任何明确提及 JavaScript 语言的问题

如果用户的请求涉及到以下方面，请分配给 Python 专家：
- Web 后端开发 (如 Django, Flask)
- 数据分析和处理 (如 Pandas, NumPy)
- 机器学习和人工智能 (如 TensorFlow, PyTorch, Scikit-learn)
- 自动化脚本和系统管理
- 任何明确提及 Python 语言的问
""")
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

route_agent = Agent(
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
event_manager = DefaultEventManager()
def on_message(message:BaseMessage):
    console.print(Panel(message.content,title="user"))
def on_response(message:BaseMessage):
    console.print(Panel(message.content,title="Assistant"))
    
event_manager.register_observer(EventType.OnMessage,on_message)
event_manager.register_observer(EventType.OnResponse,on_response)

route_agent.bind_tool("handoff_js_agent",handoff_js_agent)
console.print(route_agent.available_tools)
result = route_agent.sync_run(human_message)
result_process(route_agent,result,event_manager,auto_call_agent=False)
```
## 记忆机制
- 记忆细胞
- 记忆碎片
- 记忆卡片
