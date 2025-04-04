# Router 
import questionary
import json
from rich.console import Console
from rich.markdown import Markdown
from typing import List
from pydantic import BaseModel,Field
from rich.panel import Panel
from azent.core import DeepSeekClient,Agent
from azent.core.message import HumanMessage,SystemMessage
from azent.core.utils import _json_schema_to_example
# 生成数据
from azent.core.message import HumanMessage,SystemMessage
from azent.core.message import ToolMessage,AIMessage,BaseMessage
from azent.handoff import handoff

from azent.utils import run_agent_loop,EventManager,EventType,Span

console = Console()

from pydantic import BaseModel,Field

class FlightDetail(BaseModel):
    origin:str = Field(title="origin of flight",description="出发城市",examples=['沈阳'])
    destination:str = Field(title="destination of flight",description="到达城市",examples=['上海'])
    price:float = Field(title="price of flight",description="机票价格",examples=[700])
    date:str = Field(title="date of flight",description="航班日期",examples=['2025年03月16日'])

class FlightDetails(BaseModel):
    flight_detail_List:List[FlightDetail] = Field("flight detail list", description="航班列表",examples=[f"""{{
flight_detail_List:[{_json_schema_to_example(FlightDetail,is_flag=False)}] 
    }}"""])

system_message = SystemMessage(content="航班数据生成，出发城市，到达城市以及票价")
human_message = HumanMessage(content="生成 10 种以上航线")
client = DeepSeekClient(name="deepseek-client")


baggae_process_agent_system_prompt = """
行李分拣与装卸：

分拣： 根据行李上的标签信息，将行李准确分拣至对应的航班或区域。
装卸： 将行李从传送带、手推车等设备上搬运至飞机货舱，或从飞机货舱卸下。
扫描： 使用扫描设备扫描行李条形码，记录行李信息，确保行李追踪。
2. 行李运输与中转：

运输： 使用行李拖车等设备将行李从一个区域运输到另一个区域，例如从分拣区到停机坪。
中转： 处理中转航班的行李，确保行李能够及时、准确地转运至下一航班。
3. 行李安全检查：

识别： 识别可疑行李，配合安检人员进行开包检查。
处理： 处理违禁品或危险品，确保飞行安全。
4. 行李信息处理：

记录： 记录行李信息，例如行李数量、重量、目的地等。
查询： 回答旅客关于行李查询的问题，协助处理行李延误或丢失等情况。
5. 其他职责：
设备维护： 维护行李处理设备，确保设备正常运行。
清洁： 保持工作区域清洁整洁。
协调： 与其他部门（例如值机、安检）协调合作，确保行李处理流程顺畅。
常见客户问题：

在工作中，行李处理工作人员经常会遇到以下客户问题：
行李延误或丢失： 旅客最关心的问题之一，需要工作人员耐心解释原因，并协助查询和处理。
行李损坏： 旅客可能因为行李在运输过程中受到挤压或碰撞而损坏，需要工作人员记录损坏情况，并协助旅客进行索赔。
行李错运： 由于分拣错误或其他原因，行李可能被运送到错误的目的地，需要工作人员及时查找并重新运送。
行李内物品遗失： 旅客可能发现行李内物品遗失，需要工作人员协助调查。
关于行李托运规定的咨询： 旅客可能对行李尺寸、重量、违禁品等规定有疑问，需要工作人员提供解答。
行李查询： 旅客想要了解行李的运输状态，需要工作人员通过系统查询并告知。
总而言之，航班处理行李工作人员的工作既繁琐又重要，他们是确保旅客行李安全、高效到达的重要环节。
"""

# 定义负责咨询机票的 Agent
flight_booking_agent = Agent(
    name="flight_booking_agent",
    handoff_description="负责处理航班预订相关的问题，例如查询航班、预订机票、更改航班、取消航班等。",
    system_message=f"""
负责处理航班预订相关的问题，例如查询航班、预订机票、更改航班、取消航班等。
""",
verbose=False
)

# 定义负责处理行李的 Agent
baggage_process_handoff_description="负责处理行李相关的问题，例如行李丢失、行李延误、行李损坏等。"

baggage_process_agent = Agent(
    name="baggage_process_agent",
    system_message=baggae_process_agent_system_prompt,
    verbose=False
)

baggage_process_agent = handoff(agent=baggage_process_agent,handoff_description=baggage_process_handoff_description)

route_agent_system_prompt = """
<responsibility>
根据顾客需求将，无需关心用户细节，
- 如果是行李和包裹问题返回 "baggage"
- 如果是航班机票相关 "flight"
<responsibility>
"""

class HandoffAgent(BaseModel):
    question:str = Field(title="question",description="用户的问题",examples=['客户咨询内容：我的行李在托运过程中丢失了，我该怎么办？'])
    agent_name:str = Field(title="agent name",description="要传递给Agent名称",examples=['baggage_process_agent'])

route_agent_system_prompt = f"""
你是一个智能代理，负责根据客户的咨询内容，选择最合适的代理来处理客户的请求。
"""
def agent_span_time(span_time):
    console.print(span_time)
agent_span = Span(on_stop=agent_span_time,auto_start=False)

route_agent = Agent(
    name="route_generator",
    system_message=route_agent_system_prompt,
    result_type=HandoffAgent,
    handoffs=[flight_booking_agent,baggage_process_agent],
    verbose=False
    )
# console.print(route_agent.system_message)
def search_baggage(baggage_number:str):
    """行李内物品遗失,行李损坏，请提供行李的编码
    """
    return f"没有找到 {baggage_number}"

event_manager = EventManager()
def on_message(message:BaseMessage):
    console.print(Panel(message.content,title="user"))
def on_response(message:BaseMessage):
    console.print(Panel(message.content,title="Assistant"))
    
event_manager.register_observer(EventType.OnMessage,on_message)
event_manager.register_observer(EventType.OnResponse,on_response)

def tool_result_handle(response):
    return response

run_agent_loop(
    agent=route_agent,
    context=None,
    cb=event_manager,
    agent_span=agent_span,
    tool_result_handle=tool_result_handle)