import os
import re
import sqlite3

from typing import Union

from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage
from azent.core import Result
from azent.core.run_context import RunContext
from azent.core.message import ErrorMessage,AIMessage

class ProviderResult(Result):
    def __init__(self,  response,messages):
        super().__init__(response)
        self.messages = messages
        self.response = response 
    def get_message(self):
        return self.messages
    def get_data(self):
        raise NotImplemented()
    def get_text(self):
        raise NotImplemented()
    


SQLITE_PROVIDER_SYSTEM_PROMPT = """
你是一位精通 SQLite 数据语句的 AI Agent。你的任务是将用户输入的任何自然语言描述或意图转换为可以直接在 SQLite 数据库上运行的有效 SQL 语句。

请注意以下几点：

* **理解用户意图:** 仔细分析用户的输入，理解他们想要查询、修改或管理数据库的哪个部分以及如何操作。
* **生成有效 SQL:** 生成的 SQL 语句必须符合 SQLite 语法，并且能够准确地实现用户的意图。
* **考虑数据库结构 (如果已知):** 如果用户在之前的对话中提供了关于数据库表结构（例如表名、列名、数据类型）的信息，请在生成 SQL 时加以利用。如果信息不足，可以做出合理的假设或在必要时向用户请求更多信息。
* **处理各种输入:** 能够处理各种类型的输入，包括但不限于：
    * 简单的查询请求（例如，“查找所有年龄大于 25 岁的用户”）
    * 复杂的查询请求（例如，“找出在过去一个月内购买了特定商品的用户及其购买总金额”）
    * 数据插入请求（例如，“添加一个名为 'John'，年龄为 30 的新用户”）
    * 数据更新请求（例如，“将 ID 为 5 的用户的年龄更新为 32”）
    * 数据删除请求（例如，“删除所有状态为 'inactive' 的记录”）
    * 表结构修改请求（例如，“向 'products' 表格添加一个名为 'price' 的 INTEGER 列”）
* **提供可直接运行的语句:** 你的输出应该是一个或多个可以直接在 SQLite 数据库连接上执行的 SQL 语句。
* **简洁明了:** 仅输出 SQL 语句，除非用户明确要求解释或其他信息。

**用户输入示例和你的预期输出：**

**用户输入:** “查询所有名为 Tony 的用户的姓名和年龄”
**你的输出:** ```sql
SELECT name, age FROM users WHERE name = 'Tony';

"""
class SqliteProvider:
    def __init__(self,
                 name,
                 db_path:str):
        
        self.name = name
        self.db_path = db_path

        def get_sqlite_connection(self,db_path):
            """
            初始化连接 SQLite 数据库并返回连接句柄。

            Args:
                db_path (str): SQLite 数据库文件的路径。

            Returns:
                sqlite3.Connection: 如果连接成功，则返回连接对象；否则返回 None。
            """
            conn = None
            try:
                conn = sqlite3.connect(db_path)
                print(f"成功连接到 SQLite 数据库: {db_path}")
                return conn
            except sqlite3.Error as e:
                print(f"连接 SQLite 数据库时发生错误: {e}")
                return None

class SqliteAgent:
    def __init__(self,name,system_prompt,db_path):
        self.name = name
        _system_prompt = system_prompt or SQLITE_PROVIDER_SYSTEM_PROMPT

        self.client = DeepSeekClient(name="deepseek-client")
        self.agent = Agent(
            name="hello_agent",
            system_message=_system_prompt,
        )
        self.db_path = db_path
        self.provider = SqliteProvider(name,db_path)

    def extract_sql_code(self,text):
        """
        从文本中提取 SQL 代码块。

        Args:
            text (str): 包含 SQL 代码的文本。

        Returns:
            list: 包含提取到的 SQL 代码块的列表。
                每个代码块都是一个字符串。
                如果未找到 SQL 代码块，则返回一个空列表。
        """
        sql_code_blocks = []
        # 查找以 "```sql" 开始和以 "```" 结束的代码块
        pattern_fenced = r"```sql\s*(.*?)\s*```"
        matches_fenced = re.findall(pattern_fenced, text, re.DOTALL)
        sql_code_blocks.extend(matches_fenced)

        # 查找以 "```" 开始和以 "```" 结束但没有 "sql" 标签的代码块
        pattern_generic_fenced = r"```\s*(.*?)\s*```"
        matches_generic_fenced = re.findall(pattern_generic_fenced, text, re.DOTALL)
        for match in matches_generic_fenced:
            # 简单判断是否可能是 SQL (可以根据需要添加更复杂的判断)
            if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", match, re.IGNORECASE):
                # 避免重复提取已经通过 ```sql 提取的代码块
                if match not in sql_code_blocks:
                    sql_code_blocks.append(match)

        # 查找不包含在代码块中的独立 SQL 语句
        pattern_standalone = r"(?:^|\n)(SELECT\s.+?;|INSERT\s.+?;|UPDATE\s.+?;|DELETE\s.+?;|CREATE\sTABLE.+?;|ALTER\sTABLE.+?;|DROP\sTABLE.+?;)(?:\n|$)"
        matches_standalone = re.findall(pattern_standalone, text, re.IGNORECASE | re.DOTALL)
        sql_code_blocks.extend([match.strip() for match in matches_standalone])

        # 去除重复的代码块 (保留原始顺序)
        seen = set()
        unique_blocks = [block for block in sql_code_blocks if not (block in seen or seen.add(block))]

        return unique_blocks
    
    def run_sqlite_commands(self,sql ):
        messages = []
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            messages.append(AIMessage(content=f"成功执行\n{sql}"))
        except sqlite3.Error as e:
            messages.append(ErrorMessage( content=f"执行 SQLite 命令时发生错误: {e}"))
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
                messages.append(AIMessage(content="数据库连接已关闭。"))

        return messages
    async def run(self,
            query:Union[str,HumanMessage],
            # TODO 有待考量具体设计
            run_context:RunContext|None=None)->Result:
        
        messages = []
        agent_result = await self.agent.run(query,run_context)
        # print(result.get_message()[0].content)
        messages.extend(agent_result.get_message())
        for sql_code in self.extract_sql_code(agent_result.get_message()[0].content):
            sql_messages = self.run_sqlite_commands(sql=sql_code)
            messages.extend(sql_messages)
        result = ProviderResult(response=None,messages=messages)
        return result
