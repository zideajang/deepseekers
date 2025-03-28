from typing import Union,Any,List
from pydantic import BaseModel,Field,field_serializer,ConfigDict
from enum import Enum,StrEnum


class MessageRole(StrEnum):
    AI = 'assistant'
    Human = 'user'
    System = 'system'

    Tool = 'tool'
    Image = 'image'
    Vidoe = 'video'
    Audio = 'audio'
    Code = 'code'
    CodeResult = 'code_result'
    Memory = 'memory'
    File = 'file'

    Thinking = "thinking"
    Error = "error"

class CodeLanguage(StrEnum):
    Python = 'pyhton'
    Clanguage = 'c'
    Javascript = 'javascript'

class BaseMessage(BaseModel):

    model_config = ConfigDict(
        json_schema_extra={
            "exclude": {"is_hidden"}
        }
    )
    # TODO 兼容字符串形式

    role:Union[MessageRole,str]
    content:Union[str,List[str]]
    # is_hidden 可见性对于是否参与 history message ，对于 LLM 模型该 message 是否可见
    is_hidden:bool = False
    
    @field_serializer('role')
    def serialize_role(self, role:Union[MessageRole,str]):
        if isinstance(role,MessageRole):
            return  role.value
        else:
            return role

# 对于心里活动的 message 对于用户为不可见
class ThingingMssage(BaseMessage):
    role:MessageRole = MessageRole.Thinking

class HumanMessage(BaseMessage):
    role:MessageRole  = MessageRole.Human
    
class SystemMessage(BaseMessage):
    role:MessageRole  = MessageRole.System

class AIMessage(BaseMessage):
    role:MessageRole  = MessageRole.AI

class ToolMessage(BaseMessage):
    role:MessageRole  = MessageRole.Tool
    tool_id:Any
    tool_call:Any
    tool_name:str
    tool_arguments:Any

class MemoryMessage(BaseMessage):
    role:MessageRole | str = MessageRole.Memory

class ImageMessage(BaseMessage):
    role:MessageRole = MessageRole.Image

class CodeMessage(BaseMessage):
    # 这里 content 是代码 
    role:MessageRole  = MessageRole.Code
    lang:str = Field(description="The language of the code.")
    
class FileMessage(BaseMessage):
    role:MessageRole | str = 'file'
    
class ErrorMessage(BaseMessage):
    role:MessageRole | str = 'error'

class CodeResultMessage(BaseMessage):
    role:MessageRole | str = 'code_result'
    file_path:str 
    
    