"""
Agent B — Private Counselor for Partner B.

Structurally identical to Agent A. Operates in complete isolation — shares
no state, no checkpointer threads, and no pgvector namespace with Agent A.

See agent_a.py for full implementation documentation.
"""
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from backend.agents.base_agent import AgentState, get_checkpointer, get_llm
from backend.agents.prompts.agent_b import build_system_prompt
from backend.memory.pgvector_store import retrieve_relevant_context

# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes (mirror of Agent A — isolated by user_id namespace)
# ─────────────────────────────────────────────────────────────────────────────

async def retrieve_context_node(state: AgentState, config: RunnableConfig) -> dict:
    user_id_str = state.get("user_id", "")
    messages = state.get("messages", [])

    query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            query = msg.content
            break

    if not query or not user_id_str:
        return {"retrieved_context": ""}

    try:
        context = await retrieve_relevant_context(uuid.UUID(user_id_str), query, k=4)
    except Exception:  # noqa: BLE001
        context = ""

    return {"retrieved_context": context}


async def generate_response_node(state: AgentState, config: RunnableConfig) -> dict:
    retrieved_context = state.get("retrieved_context", "")
    system_prompt = build_system_prompt(retrieved_context)

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    llm = get_llm(temperature=0.75)
    response = await llm.ainvoke(messages, config=config)

    return {"messages": [response]}


# ─────────────────────────────────────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────────────────────────────────────

_graph = None


async def init_agent_b() -> None:
    global _graph
    checkpointer = await get_checkpointer()
    builder = StateGraph(AgentState)
    builder.add_node("retrieve_context", retrieve_context_node)
    builder.add_node("generate_response", generate_response_node)
    builder.add_edge(START, "retrieve_context")
    builder.add_edge("retrieve_context", "generate_response")
    builder.add_edge("generate_response", END)
    _graph = builder.compile(checkpointer=checkpointer)


def get_agent_b_graph():
    if _graph is None:
        raise RuntimeError("Agent B not initialised. Call init_agent_b() first.")
    return _graph


async def chat(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    user_message: str,
    couple_id: uuid.UUID | None = None,
) -> str:
    graph = get_agent_b_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": str(user_id),
        "session_id": str(session_id),
        "couple_id": str(couple_id) if couple_id else None,
        "retrieved_context": "",
    }

    config: RunnableConfig = {"configurable": {"thread_id": f"{user_id}:{session_id}"}}
    result = await graph.ainvoke(initial_state, config=config)

    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    return ai_messages[-1].content if ai_messages else "I'm here with you. Take your time."
