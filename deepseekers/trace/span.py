from abc import ABC,abstractmethod


# 设置状态机 
# pendding/processing/finish
class Span(ABC):
    def __init__(self,name,trace):
        self.name = name
        self.trace = trace
        self.current_marked:bool = False
        self.span_time:float = 0.0
        
    def reset(self):
        self.span_time = 0.0

    @abstractmethod
    def start(self):
        raise NotImplementedError()


    @abstractmethod
    def end(self):
        raise NotImplementedError()
    
class AgentRunSpan(Span):

    def __init__(self,name,agent):
        self.name = name
        self.agent = agent
        self.agent.span = self
        super().__init__(name)
    
    def start(self):
        return super().start()
