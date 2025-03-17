
from typing import Any,Protocol
from deepseekers.core import Agent
from deepseekers.core.context_manager import ContextManager

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

