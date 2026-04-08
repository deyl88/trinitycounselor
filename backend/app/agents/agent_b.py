"""Agent B — Partner B's private counselor graph.

Structurally identical to agent_a.py. The differentiation between
Agent A and Agent B is in:
  1. The JWT partner_tag ("partner_b") which scopes the memory namespace
  2. The system prompt (build_agent_b_system_prompt)
  3. The pgvector namespace ("agent_b:{relationship_id}")

The graph topology, nodes, and routing are identical.

See agent_a.py for full graph documentation.
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


def build_agent_b_graph():
    """Build and compile the Agent B LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("generate_response", generate_response)
    graph.add_node("crisis_check", crisis_check)
    graph.add_node("store_memory", store_memory)
    graph.add_node("crisis_escalation", crisis_escalation)

    graph.set_entry_point("retrieve_memory")
    graph.add_edge("retrieve_memory", "generate_response")
    graph.add_edge("generate_response", "crisis_check")

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


agent_b_graph = build_agent_b_graph()
