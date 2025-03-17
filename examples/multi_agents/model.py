from pydantic import BaseModel,Field
from typing import List,Dict
from enum import Enum,StrEnum

class DishCategory(StrEnum):
    Appetizers = "开胃菜"
    MainCourses = "主菜"
    Desserts = "甜品"

class Dish(BaseModel):
    name:str = Field(title="name of dish",description="菜品的名称",examples=['锅包肉','地三鲜'])
    price:float = Field(title="price of dish",description="菜品的价格",examples=[38.0,28.0])
    category:DishCategory = Field(title="category of dish",description="菜品属于哪一个类别，例如开胃菜、主菜还是甜品",examples=[DishCategory.MainCourses,DishCategory.MainCourses])

class RestaurantDish(BaseModel):
    dishes:List[Dish] = Field(title="dishes of restaurant",description="餐厅经营的菜品，主要分 3 类，开胃菜、主菜和甜品")

dishes = []

dishes.append(Dish(name="锅包肉",price=38.00,category=DishCategory.MainCourses))
dishes.append(Dish(name="地三鲜",price=28.00,category=DishCategory.MainCourses))
dishes.append(Dish(name="宫保鸡丁",price=32.00,category=DishCategory.MainCourses))
dishes.append(Dish(name="东北乱炖",price=32.00,category=DishCategory.MainCourses))
dishes.append(Dish(name="小甜汤",price=12.00,category=DishCategory.Desserts))
dishes.append(Dish(name="玉米羹",price=8.00,category=DishCategory.Desserts))
dishes.append(Dish(name="米糕(小份)",price=5.00,category=DishCategory.Desserts))
dishes.append(Dish(name="米糕(大份)",price=8.00,category=DishCategory.Desserts))
dishes.append(Dish(name="凉拌黄瓜",price=8.00,category=DishCategory.Appetizers))
dishes.append(Dish(name="皮蛋豆腐",price=12.50,category=DishCategory.Appetizers))
dishes.append(Dish(name="炸花生米",price=18.00,category=DishCategory.Appetizers))

restaurant_dishes = RestaurantDish(dishes=dishes)

# order
class Order:
    def __init__(self):
        self.dish_dict:Dict[str,int] = {}
        self.total_price = 0.0

    def add_dish(self,dish_name)->str:
        if dish_name not in [dish.name for dish in restaurant_dishes.dishes]:
            return f"您要点 {dish_name} 不再我们经营范围"
        else:
            if dish_name in self.dish_dict:
                self.dish_dict[dish_name] += 1
                ordered_dish:Dish|None = list(filter(lambda dish: dish.name == dish_name, restaurant_dishes.dishes))[0]
                if ordered_dish:
                    self.total_price += ordered_dish.price
                else:
                    raise ValueError("没有找到...")
                return f"您又点了一份{dish_name}"
            else:
                self.dish_dict[dish_name] = 1
                ordered_dish:Dish|None = list(filter(lambda dish: dish.name == dish_name, restaurant_dishes.dishes))[0]
                if ordered_dish:
                    self.total_price += ordered_dish.price
                else:
                    raise ValueError("没有找到...")
                return f"您刚刚点了一份{dish_name}"
    
    def remove_dish(self,dish_name)->str:
        if dish_name not in [dish.name for dish in restaurant_dishes.dishes]:
            return f"您要点 {dish_name} 不再我们经营范围"
        else:
            if dish_name in self.dish_dict:
                self.dish_dict[dish_name] -= 1
                ordered_dish:Dish|None = list(filter(lambda dish: dish.name == dish_name, restaurant_dishes.dishes))[0]
                self.total_price -= ordered_dish.price
                if self.dish_dict[dish_name] == 0:
                    self.dish_dict.pop(dish_name)
                return f"为您取消点{dish_name}"
            else:
                
                return f"您还没有点过{dish_name}，所以不用取消"

    def show_order(self)->str:
        if self.dish_dict:
            return f"您点了 {"、".join(list(self.dish_dict.keys()))}, 一共消费了 {self.total_price}"
        else:
            return f"您订单是空的，还没有开始点餐"


order = Order()



