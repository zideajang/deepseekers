from deepseekers.core import Agent
from deepseekers.core import Result,DeepseekResult
from deepseekers.core.context_manager import ContextManager

class HumanFeedBackResult(Result):
    def get_data(self):
        return super().get_data()
    
    def get_message(self):
        return super().get_message()
    
    def get_text(self):
        return super().get_text()

class UserProxyAgent(Agent):
    def run(self, query, run_context = None):
        return super().run(query, run_context)