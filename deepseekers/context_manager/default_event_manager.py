from typing import Dict,List,Callable
from deepseekers.context_manager import EventManager,EventType
class DefaultEventManager(EventManager):

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
