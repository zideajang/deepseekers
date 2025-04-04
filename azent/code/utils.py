
from typing import Union,List,Tuple,Dict,Any

import re
import os
import sys
import subprocess

from loguru import logger

WORKING_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extensions")
UNKNOWN = "unknown"
TIMEOUT_MSG = "Timeout"
DEFAULT_TIMEOUT = 600
WIN32 = sys.platform == "win32"
PATH_SEPARATOR = WIN32 and "\\" or "/"
CODE_BLOCK_PATTERN = r"```[ \t]*(\w+)?[ \t]*\r?\n(.*?)\r?\n[ \t]*```"

def content_str(content: Union[str, List[Dict[str, Any]], None]) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise TypeError(f"content must be None, str, or list, but got {type(content)}")

    rst = ""
    for item in content:
        if not isinstance(item, dict):
            raise TypeError("Wrong content format: every element should be dict if the content is a list.")
        assert "type" in item, "Wrong content format. Missing 'type' key in content's dict."
        if item["type"] == "text":
            rst += item["text"]
        elif item["type"] == "image_url":
            rst += "<image>"
        else:
            raise ValueError(f"Wrong content format: unknown type {item['type']} within the content")
    return rst
def extract_code(
    text: Union[str, List], pattern: str = CODE_BLOCK_PATTERN, detect_single_line_code: bool = False
) -> List[Tuple[str, str]]:
    # text = content_str(text)
    text  = text[0]
    if not detect_single_line_code:
        match = re.findall(pattern, text, flags=re.DOTALL)
        return match if match else [(UNKNOWN, text)]

    # Extract both multi-line and single-line code block, separated by the | operator
    # `([^`]+)`: Matches inline code.
    code_pattern = re.compile(CODE_BLOCK_PATTERN + r"|`([^`]+)`")
    code_blocks = code_pattern.findall(text)

    # Extract the individual code blocks and languages from the matched groups
    extracted = []
    for lang, group1, group2 in code_blocks:
        if group1:
            extracted.append((lang.strip(), group1.strip()))
        elif group2:
            extracted.append(("", group2.strip()))

    return extracted
    

def get_powershell_command():
    try:
        result = subprocess.run(["powershell", "$PSVersionTable.PSVersion.Major"], capture_output=True, text=True)
        if result.returncode == 0:
            return "powershell"

    except FileNotFoundError:
        # This means that 'powershell' command is not found so now we try looking for 'pwsh'
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return "pwsh"

        except FileNotFoundError:
            if WIN32:
                logger.warning("Neither powershell nor pwsh is installed but it is a Windows OS")
            return None


powershell_command = get_powershell_command()

def _cmd(lang):
    if lang.startswith("python") or lang in ["bash", "sh", powershell_command]:
        return lang
    if lang in ["shell"]:
        return "sh"
    if lang in ["ps1", "pwsh", "powershell"]:
        return powershell_command

    raise NotImplementedError(f"{lang} not recognized in code execution")
