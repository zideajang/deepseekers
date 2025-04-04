from typing import Any
from abc import ABC,abstractmethod
from azent.core import Agent
from contextlib import contextmanager

class Trace(ABC):
    def __init__(self,name):
        self.name = name

    @abstractmethod
    def on_event(self,span,metadata:Any):
        raise NotImplementedError()

@contextmanager
def trace(agent:Agent):
    agent
