from typing import List,Literal,Protocol,Any,TypeVar,Generic
import pandas as pd
from pydantic import BaseModel,Field
from deepseekers.core import Agent,Result

T = TypeVar('T')


class BaseProvider(Protocol):
    
    def run_command(self,commond):
        ...
    def extract_command(self,result:Result):
        ...
    def to_schema(self):
        ...

class BaseProviderContext(BaseModel,Generic[T]):
    type:str = Field(title="上下文类型",description="上下文类型为 DataFrame")
    data:T


class BaseProviderResponse[T](BaseModel):
    status:Literal["success","error"] = Field(title="响应的状态",examples=["success"])
    result_type:type
    results:List[T]