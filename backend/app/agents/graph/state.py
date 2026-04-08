"""LangGraph agent state definitions.

AgentState is the shared mutable state threaded through every node
in the agent graph. LangGraph passes state between nodes and handles
reducer logic for accumulated fields (like ``messages``).

The ``add_messages`` reducer appends to the messages list rather than
replacing it — this is the standard LangGraph pattern for chat memory.
"""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Mutable state threaded through the Agent A / Agent B graph nodes.

    Fields
    ──────
    messages
        Accumulated LangChain message objects (HumanMessage, AIMessage).
        The ``add_messages`` reducer appends each new message rather than
        overwriting the list — standard LangGraph chat pattern.

    user_id
        UUID string of the authenticated user. Used to scope memory lookups
        and enforce namespace isolation in pgvector.

    partner_id
        UUID of the other partner in this relationship. Never used to access
        private data — only for RKG context in Agent R.

    relationship_id
        UUID of the relationship. Used as part of the memory namespace and
        for RKG queries.

    agent_role
        "agent_a" | "agent_b" | "agent_r"
        Drives namespace selection and prompt selection.

    partner_name
        Display name of the user (not their partner). Injected into the
        system prompt for warm, personalised responses.

    retrieved_memories
        Top-k semantically relevant past exchanges fetched by retrieve_memory.
        Formatted and injected into the system prompt context section.

    therapeutic_summary
        Running compressed summary of the session arc. Injected into the
        system prompt context section alongside retrieved_memories.

    response
        Final string response produced by generate_response.
        Returned to the caller after store_memory completes.

    pending_sap_signals
        Abstracted SAP signals extracted inline during generate_response.
        Written to the sap_signals_staging table by store_memory for
        async pickup by the Privacy Mediator.

    crisis_detected
        True if crisis_check identified suicidal ideation, self-harm, or
        domestic violence signals in the current exchange.

    crisis_severity
        Float 0.0–1.0 severity estimate from crisis_check. Above
        settings.crisis_intensity_threshold triggers LLM classification.
    """

    messages: Annotated[list, add_messages]
    user_id: str
    partner_id: str
    relationship_id: str
    agent_role: str
    partner_name: str
    retrieved_memories: list[dict[str, Any]]
    therapeutic_summary: str
    response: str
    pending_sap_signals: list[dict[str, Any]]
    crisis_detected: bool
    crisis_severity: float
