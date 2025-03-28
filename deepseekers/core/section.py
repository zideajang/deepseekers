from abc import ABC,abstractmethod

class Section(ABC):
    def __init__(self,name,title,description):
        self.name = name
        self.title = title
        self.description = description