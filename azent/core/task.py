
from typing import Any,Protocol
from azent.core import Agent
from azent.core.context_manager import ContextManager

from contextlib import contextmanager

class TaskInterface(Protocol):
    def setup(self):
        ...
    
    def start(self):
        ...

    def end(self):
        ...

@contextmanager
def create_task(task:TaskInterface,context:ContextManager):
    task.setup()
    yield context
    task.end()

