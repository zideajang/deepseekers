import os
import json
from typing import List,Any
import pickle

import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from tqdm import tqdm

from pydantic import BaseModel,Field
from ollama import ChatResponse, chat

from azent.core.utils import _json_schema_to_example
from azent.text_splitter import Doc
from azent.core import Agent,Client

import glob
workspace_dir = "./examples/blog_generation/workspace/"
chunking_dir = "chunking"
source_file_paht = "./data/openai_agent_sdk.txt"
blog_title = ""
blog_topic  = "OpenAI Agent SDK"
goal = f"基于给定英文资料写一篇关于{blog_topic}的可以博客论文。"

chunking_prompt = """
"Please analyze the provided text and split it into individual sentences based on semantic meaning. Ensure that each sentence is complete and conveys a clear idea or thought. If the text contains complex structures or conjunctions, break them into logical, standalone sentences while preserving the original meaning."

EXAMPLE INPUT:
"The meeting was postponed due to bad weather, and it will be rescheduled next week. Everyone should check their emails for updates."

EXPECTED OUTPUT:
{{
"output":[
    "The meeting was postponed due to bad weather.",
    "It will be rescheduled next week.",
    "Everyone should check their emails for updates."
]
}}
"""
CHUNKING_STEP = 1000

console = Console()
def preprocess_file(file_path:str):
    with open(file_path,'r',encoding='utf-8') as f:
        content = f.read()
    console.print(f"size of file:{len(content)}")
    content = content.replace('\n',' ')
    start = 0
    end = len(content)
    chunking_size_strategy = [[i, min(i + CHUNKING_STEP, end)] for i in range(start, end, CHUNKING_STEP)]
    for chunking_size in tqdm(chunking_size_strategy):
        if chunking_size[0] == 0:
            pass
        else:
            chunking_size[0] = chunking_size[0] - 50

        if chunking_size[1] == end:
            pass
        else:
            chunking_size[1] = chunking_size[1] + 50

        chunking_content = content[chunking_size[0]:chunking_size[1]]

        # print(f"{str(chunking_size[0])}_{chunking_size[1]}")

        response = chat(model="qwen2.5",messages=[{
            "role":"system","content":chunking_prompt,
            "role":"user","content":f"""
    CONTENT
    {chunking_content}
    将 CONTENT 按照语法和语义拆分为若干句子,输出给是为 LIST，
    ONLY  EXPECTED OUTPUT
    {{"output":[句子1,句子2,....]}}
    """
        }],format='json')

        # console.print(json.loads(response.message.content))
        
        with open(f'{workspace_dir}/chunking/chunking_{chunking_size[0]}_{chunking_size[1]}.pickle', 'wb') as f:
            console.print(f"将数据保存到{workspace_dir}/chunking/chunking_{chunking_size[0]}_{chunking_size[1]}.pickle")
            pickle.dump(json.loads(response.message.content), f)
        

def generate_doc():
    docs = []
    missing_doc_count = 0
    for file_path in glob.glob(f"{workspace_dir}/chunking/*.pickle"):
        with open(file_path, 'rb') as file:
            data = pickle.load(file)
            for idx, sentence in enumerate(data['output']):
                try:
                    docs.append(Doc(content=sentence,metadata={
                        "sentence_id":f"{str(os.path.basename(file_path)).replace(".pickle","")}_{idx}"
                    }))
                except:
                    missing_doc_count += 1
                    console.print(f"{missing_doc_count}")
        
    with open(f'{workspace_dir}/docs.pickle', 'wb') as f:
        pickle.dump(docs, f)
# topic_generate
# 
# def translation_step():
#     with open(f'{workspace_dir}/docs.pickle', 'rb') as f:
#         docs = pickle.load(f)
    


def blog_gen_system_prompt(topic):
    ...

class BlogSection(BaseModel):
    title:str = Field(title="title of section",description="章节标题",examples=["快速入门"])
    content:str = Field(title="content of section",description="章节的内容",examples=["在人工智能的大潮中，各大科技公司不断推出新工具，以提升开发者和企业的创作效率。2025年3月12日凌晨，OpenAI正式开源了其首个Agent SDK，并发布了Responses API。这一举措旨在简化智能体的开发流程，并为AI智能体的协作提供全新的可能性。本文将深入分析这两项技术的核心功能及其开创行业的新机遇。"])
    summary:str = Field(title="summary of secion",description="对于章节内容",examples=["2025年3月12日，OpenAI开源了其首个Agent SDK并发布了Responses API，旨在简化智能体开发流程，推动AI智能体协作，为行业带来新的发展机遇。"])


class Outline(BaseModel):
    chapter:str = Field(title="chaper",description="章节名称",examples=['引言'])
    summary:str = Field(title="summary",description="章节概要",examples=['介绍OpenAI新发布的Python Agent SDK，强调其开源特性、强大的功能如工具、交接和防护栏，以及内置的追踪功能。'])
    content:str = Field(title="content of section",description="也就是章节相关语句",examples=["原文内容"])
class BlogOutline(BaseModel):
    title:str =  Field(title="title of section",description="章节标题",examples=["快速入门"])
    outline:List[Outline] =  Field(title="summary of secion",description="对于章节内容",examples=[f"[{_json_schema_to_example(Outline,is_flag=False)}]"])

class Blog(BaseModel):
    title:str = Field(title="title of section",description="文章的标题",examples=["重磅！OpenAI开源首个Agent SDK，反击Manus"])
    sections:List[BlogSection] = Field(title="sections",description="文章章节",examples=[f"[{_json_schema_to_example(BlogSection,is_flag=False)}]"])


if __name__ == "__main__":
    # chunking
    # preprocess_file("./data/openai_agent_sdk.txt")
    # 生成文档
    # generate_doc()

    # console.print(_json_schema_to_example(Blog))
    with open(source_file_paht,'r',encoding='utf-8') as f:
        content = f.read()
    console.print(f"size of file:{len(content)}")
    content = content.replace('\n',' ')

    outline_generation_system_prompt = f"""
    请你阅读以下文章，并根据文章内容生成一篇博客的大纲。大纲需要包括以下内容：
        标题（title）：为博客拟定一个简洁且吸引人的标题。
        章节概要（outline）：将文章内容划分为若干章节，并为每个章节提供一个简短的概要。
        章节内容（content）：将 CONTEXT 相关内容内容放在 content 记录
    CONTENT
    {content}
    """


    outline_generation_agent = Agent(
        name="outline_generation",
        system_message=outline_generation_system_prompt,
        result_type=BlogOutline,
        verbose=False,
        is_debug=True
    )

    translation_system_message = """
请你根据提供的英文资料完成以下任务：

翻译：将英文资料准确翻译为中文。

加工处理：对翻译后的内容进行优化，确保语言流畅、逻辑清晰，并符合科技文章的风格。

扩写：在原文基础上补充相关背景、技术细节或案例分析，使内容更加丰富且具有深度。

风格要求：保持科技风格，语言简洁、专业，适当使用技术术语，避免过于口语化。
"""

    translation_agent = Agent(
        name="translation_agent",
        system_message=outline_generation_system_prompt,
        verbose=False,
        is_debug=False
    )

    is_stranslated = True

    # console.print(outline_generation_agent.messages)
    result = outline_generation_agent.run("根据文章内容 CONTEXT 生成结构清晰、内容丰富的博客大纲，帮助用户快速整理和输出高质量的文章的大纲。")
    for outline in  result.get_data().outline:
        console.print(outline.chapter,justify="center",style="cyan bold")
        console.print(outline.summary)
        with open(f'{outline.chapter}.pkl', 'rb') as file:
            response = pickle.load(file)
            print(response.get_message()[0].content)
        

        if not is_stranslated:
            result = translation_agent.run(f"""
    章节名称:\n
    {outline.chapter}
    章节概要:\n
    {outline.summary}
    英文资料：\n
    {outline.content}
    """)
            with open(f'{outline.chapter}.pkl', 'wb') as file:
                pickle.dump(result,file)
        


    
    # console.print(content)

    

    
   