import questionary
import json
from rich.console import Console
from examples.multi_agents.model import restaurant_dishes

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel

from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
from azent.core.message import ToolMessage,AIMessage
from azent.core.utils import _json_schema_to_example,print_config,function_to_json
from examples.multi_agents.tools import order_dish,cancel_dish,show_menu,show_order,order_dishes
from examples.multi_agents.model import restaurant_dishes
console = Console()
console.print("🧑‍🍳\t欢迎光临",justify="center",style="green bold")
# 🧑‍🍳 本店主要经验餐品

# console.print(table)

client = DeepSeekClient(name="deepseek-client")
waiter_system_message = SystemMessage(content=f"""
您是一名饭店的服务员，名字叫小张，协助顾客进行点餐，态度热情诚恳。
<context>
这是一家连锁经营的店铺，是 12 号店铺, 饭店名字 zidea 小店, 招牌菜是 **锅包肉** 和**地三鲜**，可以推荐用户。
</contex>
饭店可以提供菜品                             
<dishes>
{restaurant_dishes.model_dump_json()}
</dishes>
<insruction>
对于客户问题如果不了解，请回答好意思，例如你们老板是谁这样的问题。回答问题范围只限菜品和<context>内容
</insruction>
<insruction>
当顾客需要推荐菜品，请严格从 <dishes> 提供的菜品中进行推荐，如何用户要询问是否有某一个菜品，基于 <dishes> 确定。如果不在 <dishes> 范围，如实反馈用户，例如不好意思，我们小店暂时没有提供您想要菜品
</insruction>
<instruction>
当用户开始下单，可以考虑将点餐内容记录下来一并处理
</instruction>
<instruction>

</instruction>

提供了一些列的方法，
<tools>
show_menu():string 向顾客展示菜单
order_dish(dish_name:string):string 将客户点餐添加到订单
order_dishes(dish_name:List[string]):string 将客户点餐添加到订单
cancel_dish(dish_name:string):string 将客户点餐添加到订单
show_order():string 查看订单
</tools>
""")

waiter_agent = Agent(
    name="waiter_restaurant",
    model_name="deepseek-chat",
    system_message=waiter_system_message,
    client=client,
    context={},
    verbose=False
    )
waiter_agent.bind_tools([order_dish,cancel_dish,show_menu,show_order,order_dishes])

def run_agent_loop():

    multiline_input = False
    counter = 0
    user_message = None

    while True:
        user_input = questionary.text(
            "你:",
            multiline=multiline_input,
            qmark=">",
        ).ask()

        if user_input.startswith("/"):
            if user_input.lower() == "/exit":
                res = questionary.confirm("欢迎下次再来").ask()
                if(res):
                    break
                else:
                    continue
            if user_input.lower() == "/tool":

                console.print(waiter_agent.available_tools)
            
            if user_input.lower() == "/config":
                print_config(waiter_agent.name,waiter_agent.model_config)

        else:
            if user_input == "":
                console.print("📢 请输入")
                continue
            user_message = HumanMessage(content=user_input)

            console.print( Panel(f" {user_message.content}",title="🧑客户"))
            
            if not user_message is None:
                result = waiter_agent.run(user_message)
                message = result.get_message()[0]

                if isinstance(message,ToolMessage):

                    console.print(f"""
工具调用 {message.tool_name}
{message.tool_name}({json.loads(message.tool_arguments)}
""")
                    tool_calling_result = waiter_agent.available_tools[message.tool_name](**json.loads(message.tool_arguments))

                    if isinstance(tool_calling_result,str):

                        waiter_agent.messages.pop()
                        
                        waiter_agent.add_message(AIMessage(content=f"这是调用工具: {message.tool_name}, 返回的结果: {tool_calling_result}"))

                        result_again = waiter_agent.run(f"根据工具返回的结果,换一种说法反馈给用户")
                        # console.print(result_again.response)
                        
                        console.print(Panel(result_again.get_message()[0].content,title="🤖:服务员"))
                    else:
                        print(result)
                else:
                    waiter_agent.add_message(message=message)
                    console.print(Panel(message.content,title="🤖:waiter"))

run_agent_loop()