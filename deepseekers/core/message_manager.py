from typing import List,Callable,Optional,Union,Dict,Any

from deepseekers.core.message import SystemMessage
from deepseekers.core.message import BaseMessage,MessageDict


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

class MessageManager:
    def __init__(self,system_message:Callable[...,SystemMessage]|SystemMessage|str|None=None):
        self.messages:List[Callable|BaseMessage|MessageDict] = []
        self._process_system_message(system_message)
    
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