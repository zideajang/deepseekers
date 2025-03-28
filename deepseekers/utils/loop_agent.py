import json
from typing import Dict,Callable,Generic,List,Any,Optional

import questionary
from prompt_toolkit.styles import Style

import questionary
from rich.console import Console
from deepseekers.core import Agent
from deepseekers.core.message import HumanMessage,AIMessage,ToolMessage

console = Console()

from deepseekers.context_manager import Span,RunContext,EventManager,EventType

def run_conversion(chat_handle,
                   quit_handle,
                   exit_message:str = "是否要推出对话"):
    while True:
        user_input = questionary.text(
            "你:",
            multiline=False,
            qmark=">",
        ).ask()

        if user_input.startswith("/"):
            if user_input.lower() == "/exit":
                res = questionary.confirm(exit_message).ask()
                if(res):
                    quit_handle()
                    break
                else:
                    continue
        else:
            if user_input == "":
                console.print("📢 请输入")
                continue
            user_message = HumanMessage(content=user_input)
            if not user_message is None:
                chat_handle(user_message)

def run_agent_loop(
        agent:Agent,
        context:RunContext,
        cb:EventManager,
        tool_result_handle:Callable[...,str|Any],
        agent_span:Optional[Span]=None,
        ):
    multiline_input = False
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
                cb.trigger_event(EventType.OnFinished)
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
            cb.trigger_event(EventType.OnMessage,user_message)
            
            if not user_message is None:
                if agent_span:
                    agent_span.start()
                # 开始运行 Agent 触发事件
                cb.trigger_event(EventType.OnStartRunAgent)
                result = agent.run(user_message)
                
                # 当结束运行 Agent 触发事件
                cb.trigger_event(EventType.OnEndRunAgent,result)

                message = result.get_message()[0]
                if isinstance(message,ToolMessage):
                    # 开始调用工具时触发事件
                    cb.trigger_event(EventType.OnStartToolCall,message)
                    tool_calling_result = agent.available_tools[message.tool_name](**json.loads(message.tool_arguments))
                    response  = tool_result_handle(agent,tool_calling_result)
                    # 结束工具调用时触发事件
                    cb.trigger_event(EventType.OnEndToolCall,response)

                    if isinstance(response,str):
                        cb.trigger_event(EventType.OnResponse,AIMessage(content=response))
                    else:
                        cb.trigger_event(EventType.OnResponse,AIMessage(content=json.dumps(response)))
                else:
                    cb.trigger_event(EventType.OnResponse,message)

                if agent_span:
                    agent_span.stop()


def select_action(options):
    custom_style = Style.from_dict({
        'answer': '#ff9d00 bold',
        'question': '',
        'instruction': '',
        'pointer': '#673ab7 bold',
        'highlighted': '#ff9d00 bold',
        'selected': '#cc5454',
        'separator': '#cc5454',
        'choices': '#0abf5b',
        'exit': '#ff0000 bold',  # Define a style for 'exit'
    })
    selected_action = questionary.select(
        "选择接下来要进行的动作",
        choices=options,
        style=custom_style
    ).ask()
    return selected_action