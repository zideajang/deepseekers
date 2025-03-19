
from pydantic import BaseModel
TOOL_CALL_RESULT_PREFIX = ""
HANDOFF_PREFIX = ""

def is_pydantic_model(obj) -> bool:
    try:
        return isinstance(obj, BaseModel) or issubclass(obj.__class__, BaseModel)
    except Exception:
        return False

def tool_call_result_prompt_template(tool_name,tool_result,query):
    # 如何判断 tool_reuslt 类型为 pydantic model 或者 classdata 还是普通 类
    if is_pydantic_model(tool_result):
        tool_result = tool_result.model_dump_json()
    return f"根据调用 {tool_name} 返回的结构 {tool_result} 回答用户的问题:\n{query}"