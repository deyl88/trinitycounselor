"""
Agent R — The Relationship Agent (Mediator / Third Presence).

Unlike Agents A and B, Agent R:
  - Has no access to either partner's private session history
  - Reads only from the RKG (abstracted patterns, cycles, attachment signals)
  - Serves as mediator in joint sessions
  - Can interact with either partner individually in a "relational overview" mode

The RKG context is injected into the system prompt at the start of each
invocation — Agent R's "memory" is the relationship's pattern history,
not any individual's private words.
"""
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from backend.agents.base_agent import AgentState, get_checkpointer, get_llm
from backend.agents.prompts.agent_r import build_system_prompt
from backend.graph.rkg_client import RKGClient

# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes
# ─────────────────────────────────────────────────────────────────────────────

async def load_rkg_context_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Load relational context from the RKG for this couple.
    The retrieved context replaces retrieved_context in state.
    """
    couple_id_str = state.get("couple_id")
    if not couple_id_str:
        return {"retrieved_context": ""}

    try:
        rkg = RKGClient()
        summary = await rkg.get_relationship_summary(uuid.UUID(couple_id_str))
        # Serialize to a string for state storage
        import json
        return {"retrieved_context": json.dumps(summary)}
    except Exception:  # noqa: BLE001
        return {"retrieved_context": ""}


async def generate_response_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Generate Agent R's response using RKG context in the system prompt.
    """
    import json

    rkg_context_str = state.get("retrieved_context", "")
    rkg_context = None
    if rkg_context_str:
        try:
            rkg_context = json.loads(rkg_context_str)
        except (ValueError, TypeError):
            rkg_context = None

    system_prompt = build_system_prompt(rkg_context)
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    llm = get_llm(temperature=0.65)  # Slightly less temperature for mediator role
    response = await llm.ainvoke(messages, config=config)

    return {"messages": [response]}


# ─────────────────────────────────────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────────────────────────────────────

_graph = None


async def init_agent_r() -> None:
    global _graph
    checkpointer = await get_checkpointer()
    builder = StateGraph(AgentState)
    builder.add_node("load_rkg_context", load_rkg_context_node)
    builder.add_node("generate_response", generate_response_node)
    builder.add_edge(START, "load_rkg_context")
    builder.add_edge("load_rkg_context", "generate_response")
    builder.add_edge("generate_response", END)
    _graph = builder.compile(checkpointer=checkpointer)


def get_agent_r_graph():
    if _graph is None:
        raise RuntimeError("Agent R not initialised. Call init_agent_r() first.")
    return _graph


async def chat(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    user_message: str,
    couple_id: uuid.UUID | None = None,
) -> str:
    """
    Process a message through Agent R (Relationship Agent).

    user_id: The partner who sent this message (A or B — treated equally)
    couple_id: Required for Agent R to load RKG context
    """
    graph = get_agent_r_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": str(user_id),
        "session_id": str(session_id),
        "couple_id": str(couple_id) if couple_id else None,
        "retrieved_context": "",
    }

    config: RunnableConfig = {"configurable": {"thread_id": f"r:{session_id}"}}
    result = await graph.ainvoke(initial_state, config=config)

    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    return ai_messages[-1].content if ai_messages else "I'm holding space for both of you."
