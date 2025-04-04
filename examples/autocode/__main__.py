import os
import glob
import re
import subprocess
from rich.console import Console

import azent
from azent.core import Project
from azent.core.utils import is_snake_case

from azent.core import Agent,DeepSeekClient

# python 的版本要求
# python 12
# python 安装 deepseekers
# python setup.py install

# js/ts/go/java/rust/c/php

console = Console()
client = DeepSeekClient(name="deepseek_client")
agent = Agent(
    name="game_developer",
    model_name="deepseek-chat",
    client=client)


def read_file(file_path: str) -> str:
    """从指定路径读取文件内容。
    Args:
        file_path: 文件路径。
    Returns:
        文件内容（字符串），如果文件不存在或读取失败，则返回空字符串。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"文件未找到：{file_path}")
        return ""
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return ""

def write_file(file_path: str, file_content: str) -> bool:
    """将内容写入指定路径的文件。
    Args:
        file_path: 文件路径。
        file_content: 要写入的文件内容。
    Returns:
        写入成功返回 True，失败返回 False。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return True
    except Exception as e:
        print(f"写入文件时发生错误：{e}")
        return False

class AutocodeProject(Project):
    def setup(self):
        if not is_snake_case(self.name):
            raise ValueError(f"{self.name}需要遵从 snake case")

        current_directory = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(current_directory, self.name,"workspace")
        if not os.path.exists(folder_path):
            # 如果文件夹不存在，则创建
            os.makedirs(folder_path)
            print(f"📁 '{self.name}' 已创建在")
        else:
            # 如果文件夹已存在，则提示
            print(f"📁 '{self.name}' 已存在，无需创建。")

        # 获取规则文件
        rules = glob.glob(f"{current_directory}/rules.*")
        if len(rules) > 0:
            # console.print(f"{rules[0]} 存在")
            self.load_rules(rules)

    def load_rules(self,rules):
        pass

    def clean(self):
        console.print(f"closing {self.name}")

# 定义项目🚀
auto_project = AutocodeProject(
    name="develop_game",
    description="开发一款打飞机的游戏",
    workspace_dir="./example/autocode/develop_game",
    tools=[write_file,read_file],
    is_cache=True
    )

@auto_project.step()
def discuss_project(project:Project):

    project_description = project.description
    system_prompt = f"""Discuss the following project Be critical and strive to improve the project and remove any errors. we do NOT need unit tests and error handling and information printing should be handled by print statements and not by logging. Do not write out the entire application but provide logic, design, architecture and pseudo cod inspirations. we also dont need marketing and other considerations like that. Be very critical and strive to eliminate errors and missing features. Do not use or refer to to any external files unless explicitly told to do so by the user. Only focus on the code and logic of the app itself:\n\nProject{project_description}
    """
    # 更新 system message
    agent.update_system_message(system_prompt)
    result = agent.run("开发一款打飞机的游戏")
    
    return result.get_text()

@auto_project.step()
def generate_code(project:Project):
    if 'discuss_project' in project.context:
        discuss_project = project.context['discuss_project']
    project_description = project.description
    system_message = f"""
    <discussion>
    {discuss_project}
    </discussion>
    You are an expert programmer. Generate code based on the {project_description} and team <discussion>. Consider all aspects of the app that is discussed and use the best provided suggestions to implement all suggested features. Do not skip over features. we do not need unit tests and error handling and information printing should be handled by print statements and not by logging. Do not use or refer to to any external files unless explicitly told to do so by the user. Wrap the code in 
    <code> full code here </code> 
    tags. return the full code as for a single file
"""
    agent.update_system_message(system_message)
    result = agent.run("开发一款打飞机的游戏")
    
    return result.get_text()



with azent.get_project(proj=auto_project) as project:
    file_path = f"./examples/autocode/{project.name}/main.py"
    # 讨论如何
    result = discuss_project(project)
    # 编码
    result_code = generate_code(project)
    
    code_pattern = re.compile(r'<code>(.*?)</code>', re.DOTALL)
    match = code_pattern.search(project.context['generate_code'])
    if match:
        code_content = match.group(1).strip()  # 提取代码并去除前后空白
        with open(file_path, 'w',encoding='utf-8') as file:
            file.write(code_content)
        print("代码已保存到 main.py 文件。")
    else:
        print("未找到 <code> 标签中的代码。")
        exit()
    
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True, check=True)
        console.print("运行结果：")
        print(result.stdout)  # 输出标准输出
        if result.stderr:
            console.print("错误信息：")
            console.print(result.stderr)  # 输出标准错误


    except subprocess.CalledProcessError as e:
        console.print(f"运行失败，错误代码：{e.returncode}")
        console.print(e.stderr)
        with open(file_path, 'r',encoding='utf-8') as file:
             code_content = file.read()
        system_prompt = f"""You are an expert programmer tasked with fixing errors in code.
<code>
{code_content}
</code>
<error>
运行失败，错误代码：{e.returncode}
{e.stderr}
</error>
Analyze the error message and fixed the code read file and fixed  correct full code  
<fixed-code> 
full fixed code        
</fixed-code>
        """
        agent.update_system_message(system_prompt)
        # agent.bind_tool("read_file",read_file)
        # agent.bind_tool("write_file",write_file)
        result = agent.run("修复获取到的代码")
        console.print(result.get_text())