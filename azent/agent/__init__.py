from typing import Protocol,Union,Any,Dict
from azent.core import Result
from azent.core.context_manager import ContextManager
from azent.core.message import HumanMessage
class BaseAgent(Protocol):
    def run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:ContextManager|Dict[str,Any]|None=None)->Result:
        ...