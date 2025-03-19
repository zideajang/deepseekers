from typing import Protocol,Union,List
from deepseekers.file_search import Doc
from .recursive_character_text_splitter import RecursiveCharacterTextSplitter
# 文档内容分割器
class Splitter(Protocol):
    def split_text(self, text)->Union[List[str],List[Doc]]:
        ...


__all__ = (
    "Splitter",
    RecursiveCharacterTextSplitter
)