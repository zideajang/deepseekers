
from pydantic import BaseModel,Field
from typing import List
from fastapi import FastAPI

def _json_schema_to_example( result_type:type):
    if not hasattr(result_type,'model_json_schema'):
        raise TypeError("现在仅支持继承 BaseModel 的类")
    res = """
EXAMPLE JSON OUTPUT"""
    json_schema = result_type.model_json_schema()
    if 'properties' in  json_schema:
        example = {}
        for k,v in json_schema['properties'].items():
             example[k] = v['examples'][0]
        res += f"""
{example}
"""
    return res

class Pizza(BaseModel):
    name:str = Field(title="name of pizza",description="披萨的名称",examples=["海鲜披萨"])
    description:str = Field(title="description of pizza",description="对于披萨的简单介绍",examples=["丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"])

class PizzaList(BaseModel):
    pizza_list:List[Pizza] = Field(title="pizza list",description="给出一个披萨列表",examples=[f"""
{_json_schema_to_example(Pizza)}
"""])
    
app = FastAPI()

@app.get("/pizzas", response_model=PizzaList)
async def get_pizzas():
    pizzas = PizzaList(pizza_list=[
        Pizza(name="海鲜披萨", description="丰富的海鲜如虾、鱿鱼和贻贝搭配番茄酱和奶酪，海洋的味道在口中爆发。"),
        Pizza(name="意大利香肠披萨", description="经典的意大利香肠披萨，搭配番茄酱和奶酪，美味可口。"),
        Pizza(name="蔬菜披萨", description="新鲜的蔬菜如蘑菇、青椒、洋葱等搭配番茄酱和奶酪，健康美味。")
    ])
    return pizzas