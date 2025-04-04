from azent.core import Agent
from azent.core.run_context import RunContext
class ToolAgent:
    def __init__(self,name,description,agent,tools):
        self.name = name
        self.description = description
        self.agent = agent
        # 绑定工具
        self.agent.bind_tools(tools)
    
    def run(self, query, run_context:RunContext = None):
        return super().run(query, run_context)