from typing import Union,List
from pydantic import BaseModel,Field
from .memory_cell import MemoryCell

class MemoryCategory(BaseModel):
    name:str = Field(title="记忆类别的名称",examples=['情景记忆'])
    title:str
    description:str = Field(title="记忆类别的描述")
    examples:List[str]



class MemoryBlock(BaseModel):
    memory_block_id:str
    memory_cells:List[MemoryCell]
    memory_entities:List[str]
    memory_category:MemoryCategory

    