from typing import List,Callable
from pydantic import BaseModel,Field

from azent.core.message import BaseMessage
from .memory_block import MemoryCategory
from .memory_cell import MemoryCell

class MemoryCategory(BaseModel):
    name:str = Field(title="记忆类别的名称",examples=['情景记忆'])
    title:str
    description:str = Field(title="记忆类别的描述")
    examples:List[str]
    fn:Callable

class MemoryBlock(BaseModel):
    memory_block_id:str
    memory_cells:List[MemoryCell]
    memory_entities:List[str]
    summary:str
    memory_knowledges:str
    memory_category:List[MemoryCategory]
    timestamp:str

class MemoyManager:
    def __init__(self):
        self.memory_category_list:List[MemoryCategory] = []

    def register_memory_category(self,memory_category:MemoryCategory):
        self.memory_category_list.append(memory_category)

    def add_memory_cell(self,message):
        pass

    def _infer_category(self,messages):
        res = []
        for memory_category in self.memory_category_list:
            if memory_category.fn(messages):
                res.append(memory_category.name)

        return res

    def add_memory_block(self,messages:List[BaseMessage]):
        category_name = self._infer_category(messages)
        category = next((cat for cat in self.memory_category_list if cat.name == category_name), None)
        if category:
            new_block = MemoryBlock(
                memory_block_id=f"{category_name}_{len(self.memory_blocks) + 1}",
                memory_category=category,
                memory_cells=[MemoryCell(content=msg.content, category=category_name, timestamp=msg.timestamp) for msg in messages]
            )
            self.memory_blocks.append(new_block)
        else:
            print(f"Memory category '{category_name}' not registered.")
    def _infer_category(self, messages: List[BaseMessage]) -> str:
        """
        Simple heuristic to infer the memory category based on the content of the messages.
        This is a placeholder and would need more sophisticated logic in a real application.
        """
        if not messages:
            return "episodic_memory"  # Default category

        first_message_content = messages[0].content.lower()

        if any(keyword in first_message_content for keyword in ["yesterday", "last week", "remember", "when"]):
            return "episodic_memory"
        elif any(keyword in first_message_content for keyword in ["what is", "capital of", "define", "meaning of"]):
            return "semantic_memory"
        elif any(keyword in first_message_content for keyword in ["how to", "can you teach me to", "practice"]):
            return "procedural_memory"
        # Add more sophisticated logic based on your specific needs
        return "episodic_memory" # Default if no specific category is inferred



if __name__ == "__main__":
    memory_manager = MemoyManager()
    memory_manager.register_memory_category(MemoryCategory(
        name="episodic_memory",
        title="情景记忆",
        description="记录个人经历的事件和它们发生的时间、地点等具体情境信息。",
        examples=["你昨天晚上吃了什么","你上次度假去了哪里"]
    ))
    memory_manager.register_memory_category(MemoryCategory(
        name="semantic_memory",
        title="语义记忆",
        description="存储关于世界的一般知识、事实、概念和语言规则。",
        examples=["你知道巴黎是法国的首都，你知道“鸟”是一种有羽毛会飞的动物。"]
    ))
    memory_manager.register_memory_category(MemoryCategory(
        name="procedural_memory",
        title="程序性记忆",
        description="存储关于技能和习惯的记忆",
        examples=["骑自行车","游泳","弹钢琴"]
    ))
    memory_manager.register_memory_category(MemoryCategory(
        name="priming",
        title="启动效应",
        description="先前的刺激会影响对后续刺激的反应，即使个体可能没有意识到先前刺激的存在。",
        examples=["{{给出例子}}"]
    ))
    memory_manager.register_memory_category(MemoryCategory(
        name="classical_conditioning",
        title="经典条件反射",
        description="通过重复配对不同的刺激，建立起新的反应模式",
        examples=["{{给出例子}}"]
    ))
