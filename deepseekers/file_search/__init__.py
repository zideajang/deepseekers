from typing import Protocol,Optional,Any,Dict,List,Union,Callable
from uuid import uuid1, UUID
from enum import StrEnum
from pydantic import BaseModel,Field
from deepseekers.core import Agent
from abc import ABC 
import ollama

from deepseekers.text_splitter import Splitter,RecursiveCharacterTextSplitter,Doc
from deepseekers.vector_store import VectorStore,ChromaStore
from deepseekers.context_manager import EventType,EventManager
from contextlib import contextmanager

# 继承于
class FileSearchEventType(StrEnum):

    OnStartLoadFile = "on_start_load_file"
    OnEndLoadFile = "on_end_load_file"

    OnStartChunking = "on_start_chunking"
    OnEndChunking = "on_end_chunking"

    OnStart = "on_start"
    OnMessage = "on_message"
    OnResponse = "on_response"
    OnStartRunAgent = "on_start_run_agent"
    OnEndRunAgent = "on_end_run_agent"
    OnStartToolCall = "on_start_tool_call"
    OnEndToolCall = "on_end_tool_call"
    OnError = "on_error"
    OnFinished = "on_finished"


class FileSearchEventManager(EventManager):

    def __init__(self):
        self.observables: Dict[FileSearchEventType, List[Callable]] = {
            event_type: [] for event_type in FileSearchEventType
        }
    
    def register_observer(self, event_type: FileSearchEventType, observer: Callable):
        self.observables[event_type].append(observer)

    def trigger_event(self, event_type: FileSearchEventType, *args, **kwargs):
        for observer in self.observables[event_type]:
            try:
                observer(*args, **kwargs)
            except Exception as e:
                print(f"Error executing observer for {event_type}: {e}")




class FileEvent(BaseModel):
    file_path:str = Field(title="file path",description="要加载文件的路径")
    content:Optional[str] = Field(title="file content",description="要加载文件的内容",default="")
    
class ChunkingEvent(BaseModel):
    strategy:str = Field(title="chunking strategy",default='recursive_character_text_splitter')

class ErrorEvent(BaseModel):
    description:str = Field(title="error description")
    detail:str = Field(title="detail of error")



def ollama_embedding_fn(chunk):
        response = ollama.embeddings(model="nomic-embed-text:latest", prompt=chunk)
        embedding = response["embedding"]
        return embedding

def ollama_embedding_fn(chunk):
    response = ollama.embeddings(model="nomic-embed-text:latest", prompt=chunk)
    embedding = response["embedding"]
    return embedding
 
@contextmanager
def chat_with_file(name:str,
    file_path:Union[str,List[str]], #文档类型字符串
    context_manager:FileSearchEventManager,
    agent:Optional[Agent]=None,
    store:Optional[VectorStore] = None,
    embedding_fn:Callable = None,
    splitter:Optional[Splitter] = None,
    **api_params):

    if embedding_fn is None:
        embedding_fn = ollama_embedding_fn

    # if agent is None:
    #     agent = Agent("rag_agent")

    if store is None:
        store:VectorStore = ChromaStore(name=f"default_{name}",embedding_fn=embedding_fn)
    
    if splitter is None:
        splitter = RecursiveCharacterTextSplitter(chunk_size=50,chunk_overlap=5)


    context_manager.trigger_event(
        FileSearchEventType.OnStartLoadFile,
        FileEvent(file_path=file_path,content="加载内容"))
    
    # 加载文件
    try:
        with open(file_path,"r",encoding='utf-8') as f:
            file_content = f.read()
        
    
    except Exception as e:
        context_manager.trigger_event(
            FileSearchEventType.OnError,ErrorEvent(description=str(e),detail=f"load {file_path} failed"))
    context_manager.trigger_event(
        FileSearchEventType.OnEndLoadFile,
        FileEvent(file_path=file_path,content=file_content))

    # chunking
    context_manager.trigger_event(FileSearchEventType.OnStartChunking,ChunkingEvent())
    docs = []
    for  text in splitter.split_text(file_content):
        docs.append(Doc(content=text,metadata={"file_path":file_path}))
    context_manager.trigger_event(FileSearchEventType.OnEndChunking,ChunkingEvent())
    
    # embedding and store
    store.add_texts(
        texts=[ doc.content for doc in docs],
        metadatas=[doc.metadata for doc in docs ],
        ids=[f"idx_{idx}" for idx in range(len(docs))]
        )
    
    yield store

    context_manager.trigger_event(FileSearchEventType.OnFinished)

    
