from deepseekers.core import Agent
from deepseekers.core import Result,DeepseekResult


class HumanFeedBackResult(Result):
    def get_data(self):
        return super().get_data()
    
    def get_message(self):
        return super().get_message()
    
    def get_text(self):
        return super().get_text()

class UserProxyAgent(Agent):
    def run(self, query, deps = None)->Result:
        
        
        DeepseekResult(response=)

        return 