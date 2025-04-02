from typing import List,Generic,Optional,Any,Annotated,NewType,Literal
import pandas as pd


from pydantic import BaseModel,Field
from deepseekers.provider import BaseProviderContext,BaseProviderResponse

class CSVProviderContext(BaseProviderContext[Any]):
    type:str = Field(title="上下文类型",description="上下文类型为 DataFrame")
    columns:Optional[List[str]] = Field(title="DataFrame 的列名")
    data:Any = Field(title="DataFrame 的数据，表示为二维数组（行和列）。每个元素可以是任意数据类型")


class CSVProviderResponse(BaseProviderResponse[Any]):
    status:Literal["success","error"] = Field(title="响应的状态",examples=["success"])
    result_type:type|str
    results:List[Any]