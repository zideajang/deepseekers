import chromadb
from  typing import List,Union
from tinychain.text_splitters import Doc

from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings",
)
class ChromaStore:
    def __init__(self, name, embedding_fn,persist_directory="chroma_db"):
        self.name = name
        self.embedding_fn = embedding_fn
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=name,embedding_function=ef)

    
    def add_texts(self, texts: List[str], metadatas: List[dict] = None, ids: List[str] = None):
        embeddings = [self.embedding_fn(text) for text in texts]
        self.collection.add(embeddings=embeddings, metadatas=metadatas, ids=ids, documents=texts)

    def query(self, query_texts: List[str], n_results: int = 5):
        query_embeddings = [self.embedding_fn(text) for text in query_texts]
        results = self.collection.query(query_embeddings=query_embeddings, n_results=n_results)
        return results