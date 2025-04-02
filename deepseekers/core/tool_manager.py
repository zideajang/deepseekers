import json
import inspect
import asyncio

from typing import Callable,Dict,List, Any, get_type_hints
from deepseekers.core.utils import function_to_json
from deepseekers.core.constants import __CTX_VARS_NAME__
from deepseekers.core.message import ToolMessage,ToolCallResultMessage
def function_to_code_string(func):
    source_code = inspect.getsource(func)
    return source_code
class ToolManager:
    def __init__(self,agent=None):
        self.available_tools:Dict[str,Callable] = {}
        self._async_available_tools: Dict[str, Callable] = {}
        self._tools = []
        self.is_smart = False
        if agent:
            self.agent = agent
            self.is_smart = True

    def add_tool(self,func_name: str,func:Callable,is_async: bool = False):
        if is_async:
            self._async_available_tools[func_name] = func
        else:
            self.available_tools[func_name] = func

    @property
    def tools(self):
        self._tools = []
        for tool_name, tool_func in self.available_tools.items():
            self._tools.append(function_to_json(tool_func))
        for tool_name, tool_func in self._async_available_tools.items():
            self._tools.append(function_to_json(tool_func))

        for tool in self._tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)
        return self._tools

    def remove_tool(self, func):
        name = getattr(func, '__name__', func)
        if name in self.available_tools:
            del self.available_tools[name]
            self._tools = [t for t in self._tools if t['name'] != name]
        elif name in self._async_available_tools:
            del self._async_available_tools[name]
            self._tools = [t for t in self._tools if t['name'] != name]
        elif isinstance(func, str):
            if func in self.available_tools:
                del self.available_tools[func]
                self._tools = [t for t in self._tools if t['name'] != func]
            elif func in self._async_available_tools:
                del self._async_available_tools[func]
                self._tools = [t for t in self._tools if t['name'] != func]

    def find_tool_by_name(self,tool_name):
        return self.available_tools.get(tool_name) or self._async_available_tools.get(tool_name)
    
    def optimize_tool(self, query):
        user_input = f"""
** tools **
"""
        for func in self.available_tools.values():
            user_input += f"""
{function_to_code_string(func)}
"""
        for func in self._async_available_tools.values():
            user_input += f"""
{function_to_code_string(func)}
"""
        result = self.agent.run(user_input)
        print(result.get_message()[0])

    def analyze_tools(self) -> Dict[str, Dict]:
        """Analyzes the available tools to understand their inputs and outputs."""
        analysis = {}
        for name, func in self.available_tools.items():
            signature = inspect.signature(func)
            return_annotation = get_type_hints(func).get('return', None)
            parameters = {}
            for param_name, param in signature.parameters.items():
                if param_name != 'self':
                    parameters[param_name] = get_type_hints(func).get(param_name, Any)
            analysis[name] = {
                "parameters": parameters,
                "return_type": return_annotation,
                "is_async": False
            }
        for name, func in self._async_available_tools.items():

            signature = inspect.signature(func)
            return_annotation = get_type_hints(func).get('return', None)
            parameters = {}
            for param_name, param in signature.parameters.items():
                if param_name != 'self':
                    parameters[param_name] = get_type_hints(func).get(param_name, Any)
            analysis[name] = {
                "parameters": parameters,
                "return_type": return_annotation,
                "is_async": True
            }
        return analysis

    def can_combine(self, tool1_name: str, tool2_name: str) -> bool:
        """Checks if the output of tool1 can be used as input for tool2."""
        analysis = self.analyze_tools()
        if tool1_name not in analysis or tool2_name not in analysis:
            return False

        output_type_tool1 = analysis[tool1_name].get("return_type")
        input_params_tool2 = analysis[tool2_name].get("parameters", {})

        if output_type_tool1 is None or not input_params_tool2:
            return False

        for param_name, param_type in input_params_tool2.items():
            if param_type == output_type_tool1:
                return True
            # Add more sophisticated type checking if needed (e.g., subclassing, etc.)

        return False

    def merge_functions(self, tool1: Callable, tool2: Callable) -> Callable | None:
        """Attempts to merge two functions if the output of the first can feed into the second."""
        tool1_name = tool1.__name__
        tool2_name = tool2.__name__
        analysis = self.analyze_tools()

        if tool1_name not in analysis or tool2_name not in analysis:
            return None

        output_type_tool1 = analysis[tool1_name].get("return_type")
        input_params_tool2 = analysis[tool2_name].get("parameters", {})

        compatible_input_param_tool2 = None
        for param_name, param_type in input_params_tool2.items():
            if param_type == output_type_tool1:
                compatible_input_param_tool2 = param_name
                break

        if compatible_input_param_tool2 is None:
            return None

        async def merged_async_function(*args, **kwargs):
            """A dynamically created asynchronous function by merging two tools."""
            # Execute the first tool
            result_tool1 = tool1(*args, **kwargs) # Assuming tool1 takes the initial input

            # Prepare arguments for the second tool
            kwargs_tool2 = {compatible_input_param_tool2: result_tool1}
            # Pass through any other relevant kwargs to tool2 if needed
            # This might require more sophisticated logic based on parameter names
            signature_tool2 = inspect.signature(tool2)
            for name, value in kwargs.items():
                if name != compatible_input_param_tool2 and name in signature_tool2.parameters:
                    kwargs_tool2[name] = value

            # Execute the second tool (assuming tool2 is also async for this merged async function)
            return await tool2(**kwargs_tool2)

        def merged_sync_function(*args, **kwargs):
            """A dynamically created synchronous function by merging two tools."""
            # Execute the first tool
            result_tool1 = tool1(*args, **kwargs) # Assuming tool1 takes the initial input

            # Prepare arguments for the second tool
            kwargs_tool2 = {compatible_input_param_tool2: result_tool1}
            # Pass through any other relevant kwargs to tool2 if needed
            # This might require more sophisticated logic based on parameter names
            signature_tool2 = inspect.signature(tool2)
            for name, value in kwargs.items():
                if name != compatible_input_param_tool2 and name in signature_tool2.parameters:
                    kwargs_tool2[name] = value

            # Execute the second tool
            return tool2(**kwargs_tool2)

        merged_function = merged_async_function if analysis[tool1_name].get("is_async") or analysis[tool2_name].get("is_async") else merged_sync_function
        merged_function.__name__ = f"{tool1_name}_then_{tool2_name}"
        merged_function.__doc__ = f"Merges {tool1_name} and {tool2_name}. Output of {tool1_name} feeds into {tool2_name}."
        return merged_function
    
    async def _execute_async_tool(self, tool_name: str, tool_arguments: Dict, tool_call_id: str) -> ToolCallResultMessage:
        tool_func = self._async_available_tools.get(tool_name)
        if not tool_func:
            return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error: Asynchronous tool '{tool_name}' not found.")

        try:
            signature = inspect.signature(tool_func)
            kwargs = {}
            for param_name, param in signature.parameters.items():
                if param_name in tool_arguments:
                    kwargs[param_name] = tool_arguments[param_name]
                elif param.default is inspect.Parameter.empty:
                    return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error: Missing required argument '{param_name}' for asynchronous tool '{tool_name}'.")
            # TODO 需要处理
            await asyncio.sleep(1)  # Add a 1-second wait
            output = await tool_func(**kwargs)
            return ToolCallResultMessage(tool_call_id=tool_call_id, output=output)
        except Exception as e:
            return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error executing asynchronous tool '{tool_name}': {e}")

    async def execute_tool(self, tool_message: ToolMessage) -> ToolCallResultMessage:
        """Executes a tool based on the provided ToolMessage."""
        tool_name = tool_message.tool_call.function.name
        tool_arguments_str = tool_message.tool_call.function.arguments
        tool_call_id = tool_message.tool_call.id

        tool_func = self.find_tool_by_name(tool_name)
        if not tool_func:
            return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error: Tool '{tool_name}' not found.")

        try:
            tool_arguments = json.loads(tool_arguments_str)
        except json.JSONDecodeError as e:
            return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error decoding tool arguments: {e}")
        analysis = self.analyze_tools().get(tool_name)
        if analysis and analysis.get("is_async"):
            return await self._execute_async_tool(tool_name, tool_arguments, tool_call_id)
        else:
            try:
                # Prepare arguments for the function call
                signature = inspect.signature(tool_func)
                kwargs = {}
                for param_name, param in signature.parameters.items():
                    if param_name in tool_arguments:
                        kwargs[param_name] = tool_arguments[param_name]
                    elif param.default is inspect.Parameter.empty:
                        return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error: Missing required argument '{param_name}' for tool '{tool_name}'.")

                output = tool_func(**kwargs)
                return ToolCallResultMessage(tool_call_id=tool_call_id, output=output)
            except Exception as e:
                return ToolCallResultMessage(tool_call_id=tool_call_id, output=f"Error executing tool '{tool_name}': {e}")



if __name__ == "__main__":
    # Example Usage:
    def get_weather(city: str) -> str:
        """Gets the current weather for a city."""
        return f"The weather in {city} is sunny."

    def summarize_text(text: str) -> str:
        """Summarizes a given text."""
        return f"Summary: {text[:20]}..."

    def translate_text(text: str, language: str="chinese") -> str:
        """Translates text to a specified language."""
        return f"Translated to {language}: {text}"

    def analyze_sentiment(text: str) -> str:
        """Analyzes the sentiment of a given text."""
        return f"Sentiment: Positive"

    tool_manager = ToolManager()
    tool_manager.add_tool("get_weather",get_weather)
    tool_manager.add_tool("summarize_text",summarize_text)
    tool_manager.add_tool("translate_text",translate_text)
    tool_manager.add_tool("analyze_sentiment",analyze_sentiment)

    print("Available Tools (JSON):")
    for tool in tool_manager.tools:
        print(json.dumps(tool, indent=2))

    print("\nTool Analysis:")
    analysis = tool_manager.analyze_tools()
    for name, info in analysis.items():
        print(f"{name}: {info}")

    print("\nCan 'get_weather' output be used as input for 'summarize_text'?", tool_manager.can_combine("get_weather", "summarize_text"))
    print("Can 'summarize_text' output be used as input for 'translate_text'?", tool_manager.can_combine("summarize_text", "translate_text"))
    print("Can 'get_weather' output be used as input for 'translate_text'?", tool_manager.can_combine("get_weather", "translate_text"))

    if tool_manager.can_combine("get_weather", "summarize_text"):
        merged_tool = tool_manager.merge_functions(get_weather, summarize_text)
        if merged_tool:
            tool_manager.add_tool(merged_tool.__name__,merged_tool)
            print("\nMerged 'get_weather' and 'summarize_text' into:", merged_tool.__name__)
            print("Result of merged tool:", merged_tool(city="Seoul"))

    if tool_manager.can_combine("summarize_text", "translate_text"):
        merged_tool_2 = tool_manager.merge_functions(summarize_text, translate_text)
        print(merged_tool_2)
        exit(0)
        if merged_tool_2:
            tool_manager.add_tool(merged_tool_2.__name__,merged_tool_2)
            print("\nMerged 'summarize_text' and 'translate_text' into:", merged_tool_2.__name__)
            print("Result of merged tool:", merged_tool_2(text="This is a long piece of text that needs to be shortened.", language="Korean"))

    print("\nUpdated Available Tools (JSON):")
    for tool in tool_manager.tools:
        print(json.dumps(tool, indent=2))

