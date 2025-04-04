from enum import StrEnum
from typing import List,Any,Dict,Callable
# TODO 继承与基础事件
class FileSearchEventType(StrEnum):
    OnStart = "on_start"
    
    OnStartLoadFile = "on_start_load_file"
    OnEndLoadFile = "on_end_load_file"


    OnStartChunking = "on_start_chunking"
    OnEndChunking = "on_end_chunking"

    OnStartRunAgent = "on_start_run_agent"
    OnEndRunAgent = "on_end_run_agent"
    
    OnStartToolCall = "on_start_tool_call"
    OnEndToolCall = "on_end_tool_call"

    OnError = "on_error"
    OnFinished = "on_finished"
# TODO 继承与基础 EventMang
class FileSearchEventManager[T]:

    def __init__(self):
        self.observables: Dict[FileSearchEventType, List[Callable]] = {
            event_type: [] for event_type in FileSearchEventType
        }
    
    def register_observer(self, event_type: FileSearchEventType, observer: Callable):
        self.observables[event_type].append(observer)

    def trigger_event(self, event_type: FileSearchEventType, *args, **kwargs):
        for observer in self.observables[event_type]:
            try:
                observer(*args, **kwargs)
            except Exception as e:
                print(f"Error executing observer for {event_type}: {e}")

