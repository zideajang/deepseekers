from typing import Protocol,Union,Any,Dict
from deepseekers.core import Result
from deepseekers.core.context_manager import ContextManager
from deepseekers.core.message import HumanMessage
class BaseAgent(Protocol):
    def run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:ContextManager|Dict[str,Any]|None=None)->Result:
        ...