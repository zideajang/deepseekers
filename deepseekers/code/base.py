from typing import Protocol, runtime_checkable,List,Union,Dict,Any
from deepseekers.core.message import AIMessage,BaseMessage,CodeMessage
from deepseekers.result.code_result import CodeResult

class CodeExtractor(Protocol):
    def extract_code_blocks(self,message:Union[str,List[BaseMessage],None,List[Dict[str,Any]]]):
        ...

    

@runtime_checkable
class CodeExecutor(Protocol):
    """用于执行代码"""
    # class 

    def code_extractor(self)->CodeExtractor:
        """"""

    def execute_code_blocks(self,code_messages:List[CodeMessage])->CodeResult:
        ...