"""Agent A — Partner A's private counselor graph.

This module assembles the LangGraph StateGraph for Agent A and exposes
a module-level compiled graph that is instantiated once at import time
and reused across all requests.

The graph is stateless between requests — all session state is stored in
pgvector and loaded at the start of each request via retrieve_memory.
LangGraph's in-process state exists only for the duration of a single invocation.

Graph topology
──────────────
  retrieve_memory → generate_response → crisis_check
                                              │
                                 ┌────────────┴────────────┐
                                 ▼                         ▼
                           store_memory          crisis_escalation
                                 │                         │
                                 └──────────► END ◄────────┘
"""

from langgraph.graph import END, StateGraph

from app.agents.graph.nodes import (
    crisis_check,
    crisis_escalation,
    generate_response,
    retrieve_memory,
    route_after_crisis_check,
    store_memory,
)
from app.agents.graph.state import AgentState


def build_agent_a_graph():
    """Build and compile the Agent A LangGraph StateGraph.

    Returns:
        A compiled LangGraph graph ready for ``ainvoke``.
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("generate_response", generate_response)
    graph.add_node("crisis_check", crisis_check)
    graph.add_node("store_memory", store_memory)
    graph.add_node("crisis_escalation", crisis_escalation)

    # Linear edges
    graph.set_entry_point("retrieve_memory")
    graph.add_edge("retrieve_memory", "generate_response")
    graph.add_edge("generate_response", "crisis_check")

    # Conditional branch after safety check
    graph.add_conditional_edges(
        "crisis_check",
        route_after_crisis_check,
        {
            "store_memory": "store_memory",
            "crisis_escalation": "crisis_escalation",
        },
    )

    graph.add_edge("store_memory", END)
    graph.add_edge("crisis_escalation", END)

    return graph.compile()


# Module-level compiled graph — compiled once on import, reused per request.
# Thread-safe: LangGraph compiled graphs are designed for concurrent invocation.
agent_a_graph = build_agent_a_graph()
