from examples.multi_agents.model import restaurant_dishes,order
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from typing import List
console = Console()

def show_menu()->str:
    """展示菜单
    """
    table = Table(title="menu of resturant")

    table.add_column("Name",style="cyan",justify="center")
    table.add_column("Price",style="cyan",justify="center")
    table.add_column("Category",style="cyan",justify="center")
    for dish in restaurant_dishes.dishes:
        table.add_row(dish.name,str(dish.price),dish.category)

    console.print(table)
    return "向顾客展示菜单"

def order_dish(dish_name:str)->str:
    """将顾客点菜品 dish_name 添加到订单
    """
    return order.add_dish(dish_name)

def cancel_dish(dish_name:str)->str:
    """将顾客取消了菜品 dish_name
    """
    return order.remove_dish(dish_name)

def show_order()->str:
    """向用户展示订单，显示已经点了什么
    """
    return order.show_order()

def order_dishes(dish_names:List[str])->str:
    """顾客点餐了一些菜品，对于多个菜品同时操作
    """
    final_result = ""
    for dish_name in dish_names:
        result = order_dish(dish_name)
        final_result += ""

    return final_result
    