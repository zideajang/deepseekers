import time
import os
from typing import Optional,ClassVar
import hashlib
import pickle
import tiktoken
from pydantic  import BaseModel,Field
from azent.core.message import BaseMessage,MessageRole
from azent.core.client import DeepSeekClient,Client

from rich.console import Console
from rich.panel import Panel

console = Console()

HASHLIB_LENGTH = 6
CACHE_DIR = "./demos/memory/cache/"

def get_hash_prefix(text):
    hash_object = hashlib.sha256(text.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig[:HASHLIB_LENGTH]


class MemoryCell(BaseModel):
    message: BaseMessage
    token_size: Optional[int] = 0
    summary: Optional[str] = None
    model_name: Optional[str] = Field(default="deepseek-chat")
    memory_id: Optional[str] = None
    memory_cache_dir:Optional[str] = Field(default=CACHE_DIR)
    _client:Client|None = None

    # Class-level attributes (shared by all instances)
    ENCODING_CACHE:ClassVar[dict] = {}
    DEFAULT_SUMMARY_PROMPT:ClassVar[str] = "请用一句话概括以下内容："
    MAX_SUMMARY_LENGTH:ClassVar[int] = 100

    def __init__(self, **data):
        super().__init__(**data)
        memory_cell = self._set_memory_id()
        if memory_cell:
            self.summary = memory_cell["summary"]
            self.token_size = memory_cell["token_size"]
        else:
            self._set_token_size()
            if self.summary is None:
                summary_content = self._generate_summary()
                memory_cell_cache_file = os.path.join(self.memory_cache_dir,f"{self.memory_id}.pkl")
                with open(memory_cell_cache_file, 'wb') as f:
                    
                    pickle.dump({
                        "summary":summary_content,
                        "token_size":self.token_size
                    },f)


    def _get_encoding(self):
        model_name = self.model_name
        if model_name not in MemoryCell.ENCODING_CACHE:
            try:
                MemoryCell.ENCODING_CACHE[model_name] = tiktoken.encoding_for_model(model_name)
            except KeyError:
                print(f"Warning: Model '{model_name}' not found. Using cl100k_base encoding.")
                MemoryCell.ENCODING_CACHE[model_name] = tiktoken.get_encoding("cl100k_base")
        return MemoryCell.ENCODING_CACHE[model_name]

    def _set_token_size(self):
        encoding = self._get_encoding()
        self.token_size = len(encoding.encode(self.message.content))

    def summarize_content(self):
        if self.message and self.message.content:
            if self._client is None:
                self._client = DeepSeekClient(name=f"summarize_{self.memory_id}")
            response = self._client.chat({
                "model":self.model_name,
                "messages":[
                    {
                        "role":"system",
                        "content":self.DEFAULT_SUMMARY_PROMPT
                    },
                    {
                        "role":"user",
                        "content":self.message.content
                    }
                ],
                "stream":False
            })
            return response.choices[0].message.content


    def _generate_summary(self):
        
        if self.message.role == MessageRole.System or self.message.role == "system":
            self.summary = self.message.content
        else:
            if self.message and self.message.content:
                content_to_summarize = self.message.content
                if len(content_to_summarize) > MemoryCell.MAX_SUMMARY_LENGTH:
                    self.summary = self.summarize_content()
                else:
                    self.summary = content_to_summarize
        return self.summary
            
        
    def _set_memory_id(self):
        summary_hash_value = get_hash_prefix(self.message.content)
        self.memory_id = summary_hash_value
        memory_cell_cache_file = os.path.join(self.memory_cache_dir,f"{summary_hash_value}.pkl")
        if os.path.exists(memory_cell_cache_file):
            try:
                with open(memory_cell_cache_file, 'rb') as f:
                    return pickle.load(f)
            except (pickle.PickleError, EOFError) as e:
                print(f"加载缓存失败: {e}")
                return None
        else:
            return None