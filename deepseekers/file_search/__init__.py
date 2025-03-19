from typing import Protocol,Optional,Any,Dict,List,Union,Callable
from uuid import uuid1, UUID
from enum import StrEnum
from pydantic import BaseModel,Field
from deepseekers.core import Agent
from abc import ABC 
import ollama

from deepseekers.text_splitter import Splitter,RecursiveCharacterTextSplitter
from deepseekers.vector_store import VectorStore,ChromaStore

from contextlib import contextmanager

class FileSearchEventType(StrEnum):
    OnStart = "on_start"
    
    OnStartLoadFile = "on_start_load_file"
    OnEndLoadFile = "on_end_load_file"


    OnStartChunking = "on_start_chunking"
    OnEndChunking = "on_end_chunking"

    OnStartRunAgent = "on_start_run_agent"
    OnEndRunAgent = "on_end_run_agent"
    
    OnStartToolCall = "on_start_tool_call"
    OnEndToolCall = "on_end_tool_call"

    OnError = "on_error"
    OnFinished = "on_finished"

class FileSearchEventManager(ABC):

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


class Doc(BaseModel,Field):
    id:uuid1 = Field(title="id",description="id",default_factory=uuid1,exclude=True)
    content:List[str] = Field(title="content",description="文本内容")
    embedding:Optional[List[Any]] = Field(title="embedding",description="内容向量形式",exclude=True,default=None)
    meta_data:Optional[Dict[str,Any]] = Field(title="meta data",description="元数据",default_factory=dict,default={})




class FileEvent(BaseModel):
    file_path:str = Field(title="file path",description="要加载文件的路径")
    content:str = Field(title="file content",description="要加载文件的内容")

class ErrorEvent(BaseModel):
    description:str = Field(title="error description")
    detail:str = Field(title="detail of error")

def ollama_embedding_fn(chunk):
        response = ollama.embeddings(model="nomic-embed-text:latest", prompt=chunk)
        embedding = response["embedding"]
        return embedding

def rag(
        name:str,
        file_path:str,
        context_manager:FileSearchEventManager,
        agent:Optional[Agent]=None,
        store:Optional[VectorStore] = None,
        embedding_fn:Callable = None,
        splitter:Optional[Splitter] = None,
        **api_params

):
    if agent is None:
        agent = Agent("rag_agent")

    if store is None:
        store = ChromaStore(name=f"default_{name}",embedding_fn=embedding_fn)


    
    
    @contextmanager
    def chat_with_file(store):

        context_manager.trigger_event(FileSearchEventType.OnStartLoadFile,FileEvent(file_path,""))
        # 加载文件
        try:
            with open(file_path,"r",encoding='utf-8') as f:
                file_content = f.read()
            
            context_manager.trigger_event(FileSearchEventType.OnStartLoadFile,FileEvent(file_path,file_content))
        
        except Exception as e:

            context_manager.trigger_event(FileSearchEventType.OnError,ErrorEvent(description=str(e),detail=f"load {file_path} failed"))

        # 切分
        

        docs = []
        for idx, text in enumerate(splitter.split_text(file_content)):
            docs.append(Doc(content=text,metadata={
                "id":f"id_{idx+1}"
            }))
                store.add_texts(
                    texts=[ doc.content for doc in docs],
                    metadatas=[doc.metadata for doc in docs ],
                    ids=[f"idx_{idx}" for idx in range(len(docs))]
                    )
                query_result = store.query([query])
                context = "<context>"
                for ctx in query_result['documents'][0]:
                    context += ctx
                context += "</context>"
                console.print(context)
                reseponse =  client.chat(
                    {
                        "model":model_name,
                        "messages":[
                            {'role':'system','content':context},
                            {'role': 'user', 'content': query}],
                        "stream":False
                        }
                        )
                
                return reseponse,query_result,docs


        
        yield store

    return chat_with_file