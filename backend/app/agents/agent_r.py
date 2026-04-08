"""Agent R — The Relationship Counselor graph.

Agent R operates from abstracted relational data only:
  - The Relational Knowledge Graph (Neo4j) — patterns, needs, events
  - Joint session history in pgvector (namespace "agent_r:{relationship_id}")
  - No access to Agent A or Agent B's private namespaces

Graph topology (extends the base with RKG enrichment)
──────────────────────────────────────────────────────
  retrieve_memory + enrich_from_rkg → generate_response → crisis_check
                                               │
                                  ┌────────────┴────────────┐
                                  ▼                         ▼
                            store_memory          crisis_escalation
                                  │                         │
                                  └──────────► END ◄────────┘

The ``enrich_from_rkg`` node is Agent R-specific: it queries the RKG
for the current relational model and injects it into state before
generate_response builds the system prompt.
"""

from __future__ import annotations

from typing import Any

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
from app.core.logging import get_logger
from app.rkg.queries import get_relational_model

logger = get_logger(__name__)


async def enrich_from_rkg(state: AgentState) -> dict[str, Any]:
    """Fetch the current relational model from Neo4j and inject into state.

    This node runs after retrieve_memory so Agent R's prompt is grounded
    in both the joint session history and the live RKG data.

    Returns:
        Partial state update with ``relational_model`` populated.
        (relational_model is passed through to build_agent_r_system_prompt
        via the configurable context dict.)
    """
    try:
        model = await get_relational_model(state["relationship_id"])
        logger.debug(
            "rkg_model_fetched",
            relationship_id=state["relationship_id"],
            pattern_count=len(model.get("active_patterns", [])),
        )
        # Store in state for the prompt builder to consume
        return {"relational_model": model}
    except Exception as exc:
        logger.warning("rkg_enrich_failed", error=str(exc))
        return {"relational_model": {}}


def build_agent_r_graph():
    """Build and compile the Agent R LangGraph StateGraph."""
    # AgentState needs relational_model field — we extend via TypedDict inheritance
    # For now we add it as an extra key (LangGraph handles extra keys gracefully)
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("enrich_from_rkg", enrich_from_rkg)
    graph.add_node("generate_response", generate_response)
    graph.add_node("crisis_check", crisis_check)
    graph.add_node("store_memory", store_memory)
    graph.add_node("crisis_escalation", crisis_escalation)

    graph.set_entry_point("retrieve_memory")
    graph.add_edge("retrieve_memory", "enrich_from_rkg")
    graph.add_edge("enrich_from_rkg", "generate_response")
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


agent_r_graph = build_agent_r_graph()
