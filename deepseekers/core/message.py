from typing import Union,List,Literal,TypedDict,Any,Optional
from pydantic import BaseModel,Field,field_serializer,ConfigDict
from enum import Enum,StrEnum

MessageRoleType = Literal['user', 'system', 'assistant']

class MessageDict(TypedDict):
    role:MessageRoleType
    content:str

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
    ToolCallResult = 'tool_call_result'
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

    role:MessageRole | str
    content:str|List[str]
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
    role:MessageRole|str = MessageRole.Thinking

class HumanMessage(BaseMessage):
    role:MessageRole|str  = MessageRole.Human
    
class SystemMessage(BaseMessage):
    role:MessageRole|str  = MessageRole.System

class AIMessage(BaseMessage):
    role:MessageRole|str  = MessageRole.AI

class ToolMessage(BaseMessage):
    role:MessageRole|str  = MessageRole.Tool
    tool_id:str
    tool_call:Any
    tool_name:str
    tool_arguments:Any

class ToolCallResultMessage(BaseMessage):
    role:MessageRole|str  = MessageRole.ToolCallResult
    tool_call_id:str|None
    content:str|List[str] = ""
    output:Optional[Any] = None

class MemoryMessage(BaseMessage):
    role:MessageRole | str = MessageRole.Memory

class ImageMessage(BaseMessage):
    role:MessageRole | str= MessageRole.Image

class CodeMessage(BaseMessage):
    # 这里 content 是代码 
    role:MessageRole | str = MessageRole.Code
    lang:str = Field(description="The language of the code.")
    
class FileMessage(BaseMessage):
    role:MessageRole | str = MessageRole.File
    
class ErrorMessage(BaseMessage):
    role:MessageRole | str = MessageRole.Error

class CodeResultMessage(BaseMessage):
    role:MessageRole | str = 'code_result'
    file_path:str 
    
    