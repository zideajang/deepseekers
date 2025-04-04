from pydantic import BaseModel,Field
from azent.core.run_context import RunContext
from azent.core import Agent
from azent.core import Result
from azent.result.fim_result import FIMResult
from azent.core.client import DeepSeekClient

# 在 FIM (Fill In the Middle) 补全中，用户可以提供前缀和后缀（可选），模型来补全中间的内容。FIM 常用于内容续写、代码补全等场景。

class FIMAgent:
    def __init__(self,
                 name:str,
                 description:str):
        self.name = name
        self.description = description

        client = DeepSeekClient(name='deepseek-client',base_url="https://api.deepseek.com/beta")
        self.agent = Agent(
            name=self.name,
            description=self.description,
            client=client,
            result_parser_type=FIMResult
        )
    def run(self, query, run_context:RunContext = None):
        # valid_run_context
        # 解析 query 需求解析为工具，
        """
        def add(a:int, b:int):int
        
        def add(url:)
        {{}}
        return 
        """

        if "prompt" not in run_context.config:
            raise ValueError(f"run_context.config 需要 prompt")
        if "suffix" not in run_context.config:
            raise ValueError(f"run_context.config 需要 suffix")
        
        result = self.agent.run(query=query,run_context=run_context)
        return result

