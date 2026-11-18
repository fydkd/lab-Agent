import datetime
from typing import Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.constants import START
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from app.config import settings
from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services import agent_tools

SYSTEM_PROMPT = """你是智能实验室预约系统的 Agent，回答要简洁。
你可以：
1. 使用 search_lab_docs 工具查询实验室文档。
2. 使用 list_open_labs / list_lab_equipment 工具查询当前有哪些开放的实验室或设备。
3. 用户进行了预约确认后，使用 create_lab_reservation 工具来创建真实的预约落库。
4. 使用 get_today 工具查询当前日期进行日期的换算。

## 必须遵守

### 日期处理
系统提示末尾已经给出了当前真实日期，涉及 今天、明天、后天、下周 等日期换算时，**必须以该日期为基准计算**，不要反问用户，更不要凭印象编造日期。get_today 工具仅作为备用校验，结果与系统提示不一致时以系统提示为准。

### 实验室 ID 准确性（极其重要）
- lab_id 必须从 list_open_labs 工具返回的结果中**逐字复制**，绝对不能凭印象猜测或编造。
- 调用 create_lab_reservation 时，**必须同时传入 lab_name 参数**（值为 list_open_labs 返回的该实验室名称），用于工具内部交叉校验。
- 如果 create_lab_reservation 返回 ok=False 且提示名称不匹配，说明你选错了 lab_id，必须重新调用 list_open_labs 并从结果中找到正确的 lab_id，
    **不要重试同一个错误的 lab_id **。
- 预约成功后，检查返回结果中的 lab_name 是否与用户要预约的实验室一致，如不一致需主动告知用户。

### 预约确认流程
在提交预约之前必须向用户复述：实验室ID与名称（或设备ID与名称）、日期、开始时间、结束时间。并得到用户确认在进行实际操作。
用户没说 【确认】【确认预约】【就这样预约】等确定性回复之前，不要调用 create_lab_reservation 工具。
工作流的确认环节里如果缺少了 lab_id 或 equipment_id，请先调用 list_open_labs / list_lab_equipment 工具查询到了lab_id 或 equipment_id再创建，不要瞎写。

### 其他
预约成功后状态是待审核，必须管理员审核通过后才能使用实验室或者设备。
不要瞎编数据库里没有的实验室或设备信息。
如果是问开放时间或者实验室规则，优先调用 search_lab_docs，不要凭空回答。
"""

def _build_system_message() -> SystemMessage:
    now = datetime.datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return SystemMessage(
        content=f"{SYSTEM_PROMPT}\n\n## 当前日期\n今天是 {now.strftime('%Y-%m-%d')}（{weekdays[now.weekday()]}），当前时间 {now.strftime('%H:%M')}。"
    )


TOOL_LABELS = {
    "list_open_labs": "查询开放实验室",
    "list_lab_equipment": "查询实验室设备",
    "create_lab_reservation": "创建预约",
    "get_today": "查询当前日期",
    "search_lab_docs": "查询实验室文档",
}


def _build_history(data: ChatRequest) -> list:
    history = []
    for message in data.messages:
        if message.role == "user" and message.content.strip():
            history.append(HumanMessage(content=message.content.strip()))
        elif message.role == "assistant" and message.content.strip():
            history.append(AIMessage(content=message.content.strip()))
    if not history:
        raise BusinessException(message="对话内容为空")
    return history


def _tool_output_preview(output: Any, limit: int = 200):
    if isinstance(output, ToolMessage):
        output = output.content
    text = (
        output if isinstance(output, str) else str(output)
    )
    return text if len(text) <= limit else text[:limit] + "..."


def _chunk_text(chunk: Any):
    if chunk is None:
        return ""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", ""))
        return "".join(parts)
    return str(content) if content is not None else ""


def build_agent(db: Session, current_user: User):
    tools = agent_tools.build_tools(db, current_user)
    llm = ChatOpenAI(
        api_key=settings.LLM_API_KEY, 
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0,
        streaming=True,   # 开启流式输出
    ).bind_tools(tools)
    
    async def agent_node(state: MessagesState):
        """langGraph 执行的工作流节点"""
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)    # 调用大模型的节点
    graph.add_node("tools", ToolNode(tools))    # tool call的节点
    graph.add_edge(START, "agent")    # 开始节点 -> 调用大模型节点
    graph.add_conditional_edges("agent", tools_condition)    # 看有无tool call，有就继续call，没有就结束，输出结果
    graph.add_edge("tools", "agent")    # 让agent看tool调用的结果
    return graph.compile()


async def stream_agent(db: Session, current_user: User, data: ChatRequest):
    """生成器：边跑agent边yield事件，提供流式输出"""
    try:
        history = _build_history(data)
        agent = build_agent(db, current_user)
        inputs = {"messages": [_build_system_message(), *history]}

        yield {"type": "status", "message": "正在思考中，请稍后..."}
        
        async for event in agent.astream_events(inputs, version="v2", config={"recursion_limit": 10}):
            kind = event.get("event")
            if kind == "on_tool_start":
                name = event.get("name") or ""
                yield {
                    "type": "tool_start",
                    "name": name,
                    "label": TOOL_LABELS.get(name, name)
                }

            elif kind == "on_tool_end":
                name = event.get("name") or ""
                yield {
                    "type": "tool_end",
                    "name": name,
                    "label": TOOL_LABELS.get(name, name),
                    "preview": _tool_output_preview((event.get("data") or {}).get("output")
                                                    )
                }
            elif kind == "on_chat_model_stream":
                metadata = event.get("metadata") or {}
                if metadata.get("langgraph_node") not in [None, "agent"]:
                    continue
                text = _chunk_text((event.get("data") or {}).get("chunk"))
                yield {"type": "token", "content": text}
        yield {"type": "done"}
    except BusinessException as e:
        yield {"type": "error", "message": e.message}
    except Exception:
        yield {"type": "error", "message": "大模型调用失败，请稍后重试"}


# def run_agent(db: Session, current_user: User, data: ChatRequest):
#     """大模型对话"""
#     if not data.messages:
#         raise BusinessException(message="对话内容为空")
#     history = []
#     for message in data.messages:
#         if message.role == "user" and message.content.strip():
#             history.append(HumanMessage(content=message.content.strip()))
#         elif message.role == "assistant" and message.content.strip():
#             history.append(AIMessage(content=message.content.strip()))
#     if not history:
#         raise BusinessException(message="请输入您要对话的内容")

#     agent = build_agent(db, current_user)
#     try:
#         result = agent.invoke(
#             {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]},
#             config={"recursion_limit": 10}
#         )   # 设置对话循环上限10轮
#     except BusinessException:
#         raise
#     except Exception:
#         raise BusinessException(message="大模型调用失败，请稍后重试")
    
#     messages = result.get("messages") or []
#     if not messages:
#         raise BusinessException(message="大模型没有返回任何内容")
#     for message in reversed(messages):
#         if isinstance(message, AIMessage) and message.content.strip():
#             content = message.content.strip()
#             if isinstance(content, list):
#                 content = "".join(
#                     part.get("text", "") if isinstance(part, dict) else str(part)
#                     for part in content
#                 )
#             if str(content).strip():
#                 return str(content).strip()
