"""
Agent A — Private Counselor for Partner A.

LangGraph implementation with:
  - Two-node graph: context retrieval → response generation
  - PostgresSaver checkpointer for stateful multi-turn memory
  - pgvector semantic retrieval for long-term cross-session context
  - EFT-informed system prompt (see prompts/agent_a.py)

Privacy guarantee: This agent's checkpointer threads are scoped to Partner A's
user_id. Agent B and Agent R have zero access to this data.
"""
import uuid
from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from backend.agents.base_agent import AgentState, get_checkpointer, get_llm
from backend.agents.prompts.agent_a import build_system_prompt
from backend.memory.pgvector_store import retrieve_relevant_context

# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes
# ─────────────────────────────────────────────────────────────────────────────

async def retrieve_context_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Semantic retrieval from the user's pgvector long-term memory store.
    Uses the last human message as the query.

    Injects retrieved context into state so the generation node can include
    it in the system prompt — enabling continuity across sessions.
    """
    user_id_str = state.get("user_id", "")
    messages = state.get("messages", [])

    if not user_id_str or not messages:
        return {"retrieved_context": ""}

    # Find the last human message to use as retrieval query
    query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            query = msg.content
            break

    if not query:
        return {"retrieved_context": ""}

    try:
        user_id = uuid.UUID(user_id_str)
        context = await retrieve_relevant_context(user_id, query, k=4)
    except Exception:  # noqa: BLE001
        # Retrieval failure is non-fatal — agent continues without context
        context = ""

    return {"retrieved_context": context}


async def generate_response_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Core response generation node.
    Builds the full system prompt (with retrieved context) and calls Claude.
    """
    retrieved_context = state.get("retrieved_context", "")
    system_prompt = build_system_prompt(retrieved_context)

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    llm = get_llm(temperature=0.75)
    response = await llm.ainvoke(messages, config=config)

    return {"messages": [response]}


# ─────────────────────────────────────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────────────────────────────────────

async def build_agent_a_graph():
    """
    Compile and return the Agent A LangGraph.
    Called once at application startup; the compiled graph is cached.
    """
    checkpointer = await get_checkpointer()

    builder = StateGraph(AgentState)
    builder.add_node("retrieve_context", retrieve_context_node)
    builder.add_node("generate_response", generate_response_node)

    builder.add_edge(START, "retrieve_context")
    builder.add_edge("retrieve_context", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile(checkpointer=checkpointer)


# Module-level graph instance — populated at app startup via init_agent_a()
_graph = None


async def init_agent_a() -> None:
    """Called once during application lifespan startup."""
    global _graph
    _graph = await build_agent_a_graph()


def get_agent_a_graph():
    if _graph is None:
        raise RuntimeError("Agent A not initialised. Call init_agent_a() first.")
    return _graph


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

async def chat(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    user_message: str,
    couple_id: uuid.UUID | None = None,
) -> str:
    """
    Process a single chat turn for Partner A.

    Args:
        user_id: Partner A's user ID (scopes the checkpointer thread)
        session_id: Active session ID
        user_message: The raw message text from Partner A
        couple_id: Set if this user is part of a couple (for RKG context later)

    Returns:
        The agent's response as a plain string.
    """
    from langchain_core.messages import HumanMessage

    graph = get_agent_a_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": str(user_id),
        "session_id": str(session_id),
        "couple_id": str(couple_id) if couple_id else None,
        "retrieved_context": "",
    }

    config: RunnableConfig = {
        "configurable": {"thread_id": f"{user_id}:{session_id}"}
    }

    result = await graph.ainvoke(initial_state, config=config)

    # Extract the last AI message
    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    if not ai_messages:
        return "I'm here with you. Take your time."

    return ai_messages[-1].content
