from typing import Protocol,List,Union
from tinychain.text_splitters import Doc

from .chrome_store import ChromaStore

class VectorStore(Protocol):
    def add_texts(self, texts: List[Union[str,Doc]], metadatas: List[dict] = None, ids: List[str] = None):
        ...

    def query(self, query_texts: List[str], n_results: int = 5):
        ...

__all__ = (
    "VectorStore",
    "ChromaStore",
)

