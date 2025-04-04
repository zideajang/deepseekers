import time
from typing import List,Callable,Dict,Optional
from enum import StrEnum
from abc import ABC,abstractmethod
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
    OnError = "on_error"
    OnFinished = "on_finished"


class EventManager[T](ABC):

    def __init__(self):
        self.observables: Dict[T, List[Callable]] = {
            event_type: [] for event_type in T
        }
    @abstractmethod
    def register_observer(self, event_type: T, observer: Callable):
        raise NotImplementedError()
    @abstractmethod
    def trigger_event(self, event_type: T, *args, **kwargs):
        raise NotImplementedError()
        


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


__all__ = (
    "RunContext",
    "EventType",
    "EventManager",
    "Span",
    "DefaultEventManager"
)