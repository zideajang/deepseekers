from typing import Dict,Callable,Generic,List,Any,Optional
import json
import time
from enum import StrEnum
from abc import ABC,abstractmethod
import questionary
from rich.console import Console
from deepseekers.core import Agent
from deepseekers.core.message import HumanMessage,AIMessage,ToolMessage

console = Console()

class RunContext[T](ABC):
    def __init__(self):
        self.context = {}
    @abstractmethod
    def get_data(self)->T:
        raise NotImplementedError()

class EventType(StrEnum):
    OnStart = "on_start"
    OnMessage = "on_message"
    OnResponse = "on_response"
    OnStartRunAgent = "on_start_run_agent"
    OnEndRunAgent = "on_end_run_agent"
    OnStartToolCall = "on_start_tool_call"
    OnEndToolCall = "on_end_tool_call"
    OnFinished = "on_finished"


class EventManager[T](ABC):

    def __init__(self):
        self.observables: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
    
    def register_observer(self, event_type: EventType, observer: Callable):
        self.observables[event_type].append(observer)

    def trigger_event(self, event_type: EventType, *args, **kwargs):
        for observer in self.observables[event_type]:
            try:
                observer(*args, **kwargs)
            except Exception as e:
                print(f"Error executing observer for {event_type}: {e}")

class Span:
    def __init__(self, 
                 on_stop:Optional[Callable[[float], None]] = None,
                 callback: Optional[Callable[[float], None]] = None, auto_start: bool = True):
        """
        初始化 Span 对象。

        Args:
            callback: 一个可选的回调函数，用于提示当前用时。
                      接受一个浮点数参数，表示已用时间（秒）。
            on_stop:回调函数，当 span 结束会调用整个回调函数
            auto_start: 指示是否在初始化时自动启动计时器。
        """
        self.callback = callback
        self.on_stop = on_stop
        self.is_running = False
        if auto_start:
            self.start()

    def start(self):
        """
        启动计时器。
        """
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True

    def elapsed(self) -> float:
        """
        返回已用时间（秒）。
        """
        if not self.is_running:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def stop(self):
        """
        停止计时器。
        """
        if self.is_running:
            self.end_time = time.time()
            if self.on_stop:
                self.on_stop(self.end_time - self.start_time)
            self.is_running = False

    def __enter__(self):
        """
        支持 with 语句。
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出 with 语句时停止计时器。
        """
        self.stop()

    def update_callback(self):
        """
        调用回调函数，提示当前用时。
        """
        if self.callback:
            self.callback(self.elapsed())


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
