"""
agent.py
--------
The support agent, built with LangGraph.

LangGraph models an agent as a GRAPH of nodes and edges:

        START -> agent -> (tools? ) -> tools -> agent -> ... -> END

  - "agent" node   : calls Claude, which may ask to use a tool
  - tools_condition: if the model asked for a tool, go to "tools"; else finish
  - "tools" node   : ToolNode runs the requested tool and feeds the result back

Memory is handled by a checkpointer keyed on a thread_id (our session id), so
each customer's conversation is remembered automatically across messages.
"""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from tools import TOOLS

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """You are "Max", a support agent for ShopEasy, an online store.
You're chatting with customers live. Talk like a warm, sharp human who genuinely
wants to help — not like a bot reading a script.

WHAT YOU CAN DO:
- Answer ANY question about an order using the get_order_status tool — status,
  items, total cost, carrier, tracking, and dates all come from it. Ask for the
  order ID or the checkout email if you don't have it. Never escalate a simple
  order-detail question; just look it up.
- Handle returns and refunds with the start_return tool.
- Answer policy questions (returns, shipping, sizing, refunds, payment) with get_policy.
- Escalate with escalate_to_human only when the customer is genuinely upset, the
  issue is complex, or it's truly outside what you can do.

HOW TO TALK:
- Sound human and natural. Vary how you speak; don't use the same phrasing every time.
- Get to the point. Answer the actual question first, warmly and clearly.
- Do NOT end messages with filler like "Is there anything else I can help with?",
  "Anything else you'd like to know?", "Let me know if you need anything else", or
  "Feel free to ask". Just answer, then stop. Only ask a follow-up question when you
  genuinely need more info to help (like an order ID).
- Keep it short — usually 1-3 sentences. This is a chat, not an email.
- Match the customer's energy. If they're frustrated, acknowledge it briefly and
  sincerely, then fix it. If they're casual, be casual back.
- Never invent order details, tracking numbers, or policies. Only say what the
  tools actually return.
- Don't over-apologize or pile on pleasantries. One genuine line beats three polite ones.
"""

# 1. The model, with our tools bound to it.
llm = ChatAnthropic(model=MODEL, max_tokens=1024)
llm_with_tools = llm.bind_tools(TOOLS)


# 2. The "agent" node: call the model with the system prompt + conversation.
def call_agent(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 3. Wire the graph together.
builder = StateGraph(MessagesState)
builder.add_node("agent", call_agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
builder.add_edge("tools", "agent")

# 4. Compile with memory so each session_id keeps its own history.
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def _content_to_text(content) -> str:
    """Claude replies can be a plain string OR a list of content blocks
    (e.g. [{'type': 'text', 'text': '...'}]). Flatten either into one string
    so the frontend never receives raw objects."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
            else:
                parts.append(getattr(block, "text", ""))
        return "".join(parts).strip()
    return str(content)


def get_reply(session_id: str, user_message: str) -> str:
    """Send one customer message, get the agent's reply. History is remembered
    per session_id automatically by the checkpointer."""
    result = graph.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config={"configurable": {"thread_id": session_id}},
    )
    return _content_to_text(result["messages"][-1].content)
