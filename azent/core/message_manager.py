import copy
from typing import List,Callable,Optional,Union,Dict,Any

import tiktoken
import ollama
import numpy as np
from numpy.linalg import norm

from pydantic import BaseModel,Field
from typing import ClassVar
from rich.console import Console
from rich.panel import Panel


from azent.core.message import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    MessageDict
    )

console = Console()

"""
对于 messages_dicts [
    {"role":"system","content":"content_one"},
    {"role":"user","content":"content_user"},
    {"role":"assistant","content":"content_assist"},
    {"role":"system","content":"content_one"},
]

定义 MessageManager 其中维护

- 添加 message (隐式转换)
- 移除 message by word by index 
- 弹出 message 
- 更新 message by index 
- 确保 system_message 如何是函数，运行时处理
"""

SIMILARITY_THRESHOLD = 0.7
MAX_TOKEN_THRESHOLD = 256




# class MemoryBlock(BaseModel):
#     name:str = Field(...,title="memory block name")
#     memory_cell:List[MemoryCell] = Field(...,default=[])

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = norm(vec1)
    norm_vec2 = norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0
    return dot_product / (norm_vec1 * norm_vec2)

def default_optim_fn(messages:List[MessageDict],similarity_threshold:float)->List[MessageDict]:
    # 获取用户 HumanMessage
    _messages = copy.deepcopy(messages)
    
    human_message = _messages.pop()
    
    if human_message['role'] != 'user':
        return messages

    query = human_message['content']
    filtered_messages: List[MessageDict] = []
    if _messages and _messages[0]['role'] == 'system':
        filtered_messages.append(_messages[0])
        start_index = 1
    else:
        start_index = 0

    try:
        query_embedding = np.array(ollama.embeddings(model='nomic-embed-text', prompt=query)['embedding'])
        historical_embeddings = {}
        for i in range(start_index, len(_messages)-1):
            message = _messages[i]
            embedding = np.array(ollama.embeddings(model='nomic-embed-text', prompt=message['content'])['embedding'])
            historical_embeddings[i] = embedding
    except ollama.OllamaAPIError:
        # If embedding generation fails, return the original messages (minus the last user message)
        return messages[:-1]

    # Calculate similarity and filter messages
    for i in range(start_index, len(_messages)-1):
        message = _messages[i]
        if i in historical_embeddings:
            similarity_score = cosine_similarity(query_embedding, historical_embeddings[i])
            console.print(f"{similarity_score=}")
            if similarity_score > similarity_threshold:
                filtered_messages.append(message)
    filtered_messages.append(human_message)
    return filtered_messages


def num_tokens_from_messages(messages, model="deepseek-chat"):
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # 每条消息的开销（role + content 等）
        for key, value in message.items():
            num_tokens += len(enc.encode(value))
    num_tokens += 2  # 回复时的额外开销
    return num_tokens

class MemoryManager:
    def __init__(self):
        pass
    def add_memorycell(self,message:BaseMessage):
        pass
    def _message_to_memorycell(self,message):
        pass
    def get_memorycell_by_summary(self,message:BaseMessage):
        pass

class MessageManager:
    def __init__(self,
                 system_message:Callable[...,SystemMessage]|SystemMessage|str|None=None,
                 optim_fn:Callable | None = default_optim_fn,
                 memory_manager:MemoryManager|None = None,
                 similarity_threshold:float = 0.5,
                    max_token_threshold:int = 128
                 
                 ):
        self.messages:List[Callable|BaseMessage|MessageDict] = []
        self._process_system_message(system_message)
        self.similarity_threshold = similarity_threshold
        self.max_token_threshold = max_token_threshold
        self.optim_fn = optim_fn
        self.total_token = 0
    def _process_system_message(self, system_message: Optional[Union[Callable[..., SystemMessage], SystemMessage, str]]):
        if system_message:
            match system_message:
                case str(content):
                    self.messages.append(SystemMessage(content=system_message))
                case _ if callable(system_message):
                    self.messages.append(system_message)
                case SystemMessage() as msg:
                    self.messages.append(msg)
                case _:
                    raise ValueError(f"Unsupported system_message type: {type(system_message)}")
    def add_message(self, message: Union[Dict, BaseMessage, str, Callable[..., BaseMessage]]):
        if isinstance(message, dict):
            if 'role' not in message or 'content' not in message:
                raise ValueError("字典消息必须包含 'role' 和 'content' 键。")
            message = BaseMessage(role=message['role'], content=message['content'])
        elif isinstance(message, str):
            message = BaseMessage(role='user', content=message)
        elif callable(message):
            try:
                # TODO 
                result = message()
                if not isinstance(result, BaseMessage):
                    raise ValueError(f"callable message must return a BaseMessage, not {type(result)}")
            except Exception as e:
                raise ValueError(f"Error calling message callable: {e}")
        elif not isinstance(message, BaseMessage):
            raise ValueError(f"不支持的消息类型: {type(message)}")
        self.messages.append(message)

    def remove_message(self, by: str, value: Any):
        if by == 'word':
            self.messages = [
                msg for msg in self.messages if not (
                    (callable(msg) and value in msg().content) or
                    (isinstance(msg, BaseMessage) and value in msg.content) or
                    (isinstance(msg, dict) and value in msg.get('content', ''))
                )
            ]
        elif by == 'index':
            try:
                index = int(value)
                if 0 <= index < len(self.messages):
                    self.messages.pop(index)
                else:
                    raise IndexError(f"索引 {index} 超出消息列表范围")
            except ValueError:
                raise ValueError("索引必须是整数")
        else:
            raise ValueError(f"不支持的移除方式: {by}. 支持 'word' 和 'index'.")

    def pop_message(self, index: int = -1) -> Union[BaseMessage, MessageDict, None]:
        if self.messages:
            try:
                message = self.messages.pop(index)
                if callable(message):
                    return message()
                return message
            except IndexError:
                print(f"索引 {index} 超出消息列表范围，无法弹出。")
                return None
        return None

    def update_message(self, index: int, new_message: Union[Dict, BaseMessage, str]):
        try:
            if 0 <= index < len(self.messages):
                if isinstance(new_message, dict):
                    if 'role' not in new_message or 'content' not in new_message:
                        raise ValueError("字典消息必须包含 'role' 和 'content' 键。")
                    self.messages[index] = BaseMessage(role=new_message['role'], content=new_message['content'])
                elif isinstance(new_message, str):
                    self.messages[index] = BaseMessage(role='user', content=new_message)
                elif isinstance(new_message, BaseMessage):
                    self.messages[index] = new_message
                else:
                    raise ValueError(f"不支持的新消息类型: {type(new_message)}")
            else:
                raise IndexError(f"索引 {index} 超出消息列表范围，无法更新。")
        except ValueError as e:
            print(f"更新消息失败: {e}")
        except IndexError as e:
            print(f"更新消息失败: {e}")

    def to_dict(self,context:Dict[str,Any]|None = None)->List[MessageDict]:
        message_dicts = []

        for message in self.messages:
            match message:
                case _ if callable(message):
                    result = message(context) if context is not None else message()
                    match result:
                        case str(content):
                            message_dicts.append({"role": "system", "content": content})
                        case BaseMessage() as msg:
                            message_dicts.append({"role": str(msg.role), "content": msg.content})
                        case dict() as msg:
                            message_dicts.append(dict)
                        case _:
                            raise ValueError(f"Callable message must return str or BaseMessage, not {type(result)}")
                case BaseMessage() as msg:
                    message_dicts.append({"role": str(msg.role), "content": msg.content})
                case dict() as msg_dict:
                    message_dicts.append(msg_dict)
                case _:
                    raise ValueError(f"Unsupported message type in messages list: {type(message)}")
                
        system_messages = [msg["content"] for msg in message_dicts if msg["role"] == "system"]
        non_system_messages = [msg for msg in message_dicts if msg["role"] != "system"]

        merged_system_content = "\n".join(system_messages)

        if system_messages:
            merged_system_dict = {"role": "system", "content": merged_system_content}
            optimized_messages_dicts = [merged_system_dict] + non_system_messages
        else:
            optimized_messages_dicts = non_system_messages

        total_token = num_tokens_from_messages(optimized_messages_dicts)
        self.total_token = total_token
        if total_token > self.max_token_threshold:
            console.print(f"启动优化 token: {total_token}",)
            optimized_messages_dicts = self.optim_fn(optimized_messages_dicts,similarity_threshold=self.similarity_threshold)
        return optimized_messages_dicts
    
if __name__ == "__main__":
    # 示例用法
    manager_one = MessageManager(system_message="我是初始系统消息。")
    def system_message_fn(context):
        # return f"{context['name']}"
        return SystemMessage(content=f"{context['name']}")
    manager_two = MessageManager(system_message=system_message_fn)
    print(manager_two.to_dict(context={"name":"test"}))

    manager_three = MessageManager(system_message=system_message_fn)
    manager_three.add_message({"role":"user","content":"i am human"})
    manager_three.add_message({"role":"system","content":"i am system"})
    print(manager_three.to_dict(context={"name":"test"}))