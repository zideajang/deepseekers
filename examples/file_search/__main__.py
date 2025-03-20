
import questionary
from rich.console import Console
from rich.panel import Panel

from deepseekers.core.message import AIMessage,SystemMessage,ToolMessage,HumanMessage
from deepseekers.file_search import chat_with_file,FileSearchEventManager,FileSearchEventType,FileEvent
from deepseekers.core import DeepSeekClient,Agent
# 
context_manager = FileSearchEventManager()
def on_start_load_file(file_event:FileEvent):
    console.print(f"开始加载{file_event.file_path}")
def on_end_load_file(file_event:FileEvent):
    console.print(f"已加载{file_event.file_path}")

def on_message(message:HumanMessage):
    console.print("on_message")
    console.print(Panel(message.content,title="user"))

def on_response(message:AIMessage):
    console.print("on response")
    console.print(Panel(message.content,title="assistant"))

context_manager.register_observer(FileSearchEventType.OnStartLoadFile,on_start_load_file)
context_manager.register_observer(FileSearchEventType.OnEndLoadFile,on_end_load_file)
context_manager.register_observer(FileSearchEventType.OnMessage,on_message)
context_manager.register_observer(FileSearchEventType.OnResponse,on_response)

from rich.console import Console
console = Console()

client = DeepSeekClient(name="deepseek-client")
system_message = SystemMessage(content="you are very help assistant")

agent = Agent(
    name="chat_with_file_agent",
    system_message=system_message,
    )


# 初始化 chat_with_file 这样
with chat_with_file(
    name="blog",
    file_path="./data/blog.txt",
    context_manager=context_manager
) as store:
    while True:
        user_input = questionary.text(
            "你:",
            multiline=False,
            qmark=">",
        ).ask()

        if user_input.startswith("/"):
            if user_input.lower() == "/exit":
                res = questionary.confirm("欢迎下次再来").ask()
                context_manager.trigger_event(FileSearchEventType.OnFinished)
                if(res):
                    break
                else:
                    continue
        else:
            if user_input == "":
                console.print("📢 请输入")
                continue
            user_message = HumanMessage(content=user_input)
            # 当发送消息时触发事件
            context_manager.trigger_event(FileSearchEventType.OnMessage,user_message)
            
            if not user_message is None:
                # 开始运行 Agent 触发事件
                context_manager.trigger_event(FileSearchEventType.OnStartRunAgent)

                # console.print(f"start")
                result = store.query("结构化输出",n_results=3)
                # console.print(result)
                # console.print("搜索结果",style="green bold",justify="center")
                context = "## CONTEXT\n"
                for doc in result['documents'][0]:
                    console.print(doc)
                    context += doc
                context += ""

                user_prompt = f"""
{context}
\n
基于 CONTEXT 提供的内容，来回答用户和问题或者指令
{user_message.content if isinstance(user_message,HumanMessage) else user_message}
"""
                context_manager.trigger_event(FileSearchEventType.OnMessage,HumanMessage(content=user_prompt))
                result = agent.run(user_prompt)
                
                # 当结束运行 Agent 触发事件
                context_manager.trigger_event(FileSearchEventType.OnEndRunAgent,result)

                message = result.get_message()[0]

                context_manager.trigger_event(FileSearchEventType.OnResponse,message)
                # if isinstance(message,ToolMessage):
                #     # 开始调用工具时触发事件
                #     context_manager.trigger_event(FileSearchEventType.OnStartToolCall,message)
                #     tool_calling_result = agent.available_tools[message.tool_name](**json.loads(message.tool_arguments))
                #     response  = tool_result_handle(agent,tool_calling_result)
                #     # 结束工具调用时触发事件
                #     context_manager.trigger_event(FileSearchEventType.OnEndToolCall,response)

                #     if isinstance(response,str):
                #         context_manager.trigger_event(FileSearchEventType.OnResponse,AIMessage(content=response))
                #     else:
                #         context_manager.trigger_event(FileSearchEventType.OnResponse,AIMessage(content=json.dumps(response)))
                # else:
                #     context_manager.trigger_event(FileSearchEventType.OnResponse,message)

                

  
    
    # for result['documents'][0]