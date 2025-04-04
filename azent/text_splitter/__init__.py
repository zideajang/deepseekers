import uuid
from uuid import uuid1

from typing import Protocol,Union,List,Optional,Any,Dict
from pydantic import BaseModel,Field
from .recursive_character_text_splitter import RecursiveCharacterTextSplitter
# 文档内容分割器

class Doc(BaseModel):
    ids:uuid1 = Field(title="id",description="id",default_factory=uuid1,exclude=True)
    content:str = Field(title="content",description="文本内容")
    embedding:Optional[Any] = Field(title="embedding",description="内容向量形式",exclude=True,default=None)
    metadata:Optional[Dict[str,Any]] = Field(title="meta data",description="元数据",default_factory=dict)


class Splitter(Protocol):
    def split_text(self, text)->Union[List[str],List[Doc]]:
        ...


__all__ = (
    "Splitter",
    "RecursiveCharacterTextSplitter",
    "Doc"
)