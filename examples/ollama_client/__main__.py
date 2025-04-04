from rich.console import Console
from rich.markdown import Markdown

from azent.core import Agent,Client,Result
from azent.client import OllamaClient
from azent.core.message import HumanMessage,SystemMessage
from azent.result import OllamaResult
console = Console()

# 初始化一个 client
ollama_client = OllamaClient(name="ollama-client")

system_message = SystemMessage(content="you are very help assistant")
human_message = HumanMessage(content="write hello world in python")

class OllamaAgent(Agent):
    def __init__(self, name, client = ..., model_name = 'deepseek-chat', context = None, system_message = None, deps_type = None, result_type = None, verbose = True):
        super().__init__(name, client, model_name, context, system_message, deps_type, result_type, verbose)
        self.ResultType = OllamaResult
    
agent = OllamaAgent(
    name="ollama_agent",
    model_name="qwen2.5:latest",
    client=OllamaClient(name="ollama_client"),
    system_message=system_message,
    )

result = agent.run(human_message)
console.print(result.get_text())
