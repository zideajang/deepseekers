from typing import Optional,Union,Any
from azent.result import Result
from azent.core.message import BaseMessage

class CodeResult(Result):
    def __init__(self, agent, response,
                 exit_code:int,code_output:str,code_file:Optional[Union[str,Any,None]]=None):
        super().__init__(agent, response)

        self.exit_code:int = exit_code
        self.code_output = code_output
        self.code_file = code_file
    def to_message(self):
        return ""
    
        
    def get_text(self):
        return self.code_output
    
    def __str__(self):
        return f"""
exit_code:{self.exit_code}
code_output:{self.code_output}
code_file:{self.code_file}
"""