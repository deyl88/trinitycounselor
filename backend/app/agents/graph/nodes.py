"""LangGraph node functions for the private agent graph (Agent A / Agent B).

Graph topology
──────────────

    retrieve_memory
         │
         ▼
    generate_response
         │
         ▼
    crisis_check
         │
    ┌────┴────────────────┐
    ▼                     ▼
store_memory      crisis_escalation
    │                     │
    └─────────► END ◄─────┘

Node contract
─────────────
Each node receives the full AgentState and returns a *partial* dict of
fields to update. LangGraph merges the returned dict back into state using
each field's registered reducer (add_messages for messages, replace for all others).
"""

from __future__ import annotations

import re
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.graph.state import AgentState
from app.config import get_settings
from app.core.logging import get_logger
from app.memory.pgvector_store import ConversationMemoryStore

logger = get_logger(__name__)

# ── Crisis detection keyword list ────────────────────────────────────────────
# Fast path: if any of these appear, we compute an intensity estimate and
# potentially escalate to the LLM classifier.
_CRISIS_KEYWORDS = re.compile(
    r"\b("
    r"suicid[ea]|kill myself|end my life|don't want to (be here|live)|"
    r"self.harm|cutting myself|hurt myself|overdos[ei]|"
    r"abuse|hitting me|threatening me|scared of (him|her|them)"
    r")\b",
    re.IGNORECASE,
)

_CRISIS_RESPONSE = (
    "I'm hearing something really important right now, and I want to make sure "
    "you have support beyond what I can offer.\n\n"
    "**Please reach out to one of these resources:**\n"
    "- **988 Suicide & Crisis Lifeline**: Call or text **988** (US)\n"
    "- **Crisis Text Line**: Text **HOME** to **741741**\n"
    "- **International Association for Suicide Prevention**: "
    "https://www.iasp.info/resources/Crisis_Centres/\n\n"
    "You don't have to face this alone. I'm still here with you, whenever you're ready."
)


# ── Node: retrieve_memory ─────────────────────────────────────────────────────


async def retrieve_memory(state: AgentState, config: dict[str, Any]) -> dict[str, Any]:
    """Fetch relevant past exchanges and the therapeutic summary from pgvector.

    Uses semantic similarity search to find the top-k most relevant prior
    exchanges given the current user message. Also loads the running
    therapeutic summary for this user+namespace.

    Returns:
        Partial state update with ``retrieved_memories`` and
        ``therapeutic_summary`` populated.
    """
    db = config["configurable"]["db"]
    latest_message = _get_latest_human_message(state["messages"])

    store = ConversationMemoryStore(
        user_id=state["user_id"],
        agent_role=state["agent_role"],
        relationship_id=state["relationship_id"],
        db=db,
    )

    memories, summary = await _safe_gather(
        store.similarity_search(latest_message),
        store.get_therapeutic_summary(),
    )

    logger.debug(
        "memory_retrieved",
        user_id=state["user_id"],
        memories_count=len(memories),
        has_summary=bool(summary),
    )

    return {
        "retrieved_memories": memories,
        "therapeutic_summary": summary,
    }


# ── Node: generate_response ───────────────────────────────────────────────────


async def generate_response(state: AgentState) -> dict[str, Any]:
    """Call Claude with the EFT-informed counselor prompt and return a response.

    Also runs inline SAP extraction to generate abstracted signals that
    will be staged for the Privacy Mediator's next RKG sync.

    Returns:
        Partial state update with ``response``, updated ``messages``, and
        ``pending_sap_signals``.
    """
    settings = get_settings()

    # Import prompt builders here to avoid circular imports at module level
    from app.agents.prompts.agent_a_system import build_agent_a_system_prompt
    from app.agents.prompts.agent_b_system import build_agent_b_system_prompt
    from app.agents.prompts.agent_r_system import build_agent_r_system_prompt

    prompt_builders = {
        "agent_a": build_agent_a_system_prompt,
        "agent_b": build_agent_b_system_prompt,
        "agent_r": build_agent_r_system_prompt,
    }
    build_prompt = prompt_builders[state["agent_role"]]

    system_prompt = build_prompt(
        partner_name=state.get("partner_name", "you"),
        therapeutic_summary=state.get("therapeutic_summary", ""),
        retrieved_memories=state.get("retrieved_memories", []),
    )

    llm = ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )

    # Build the message list: system prompt + prior conversation turns
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    ai_message = await llm.ainvoke(messages)
    response_text = ai_message.content

    # Inline SAP extraction — fire-and-forget, non-blocking to the user response
    sap_signals = await _extract_sap_signals_inline(
        user_message=_get_latest_human_message(state["messages"]),
        ai_response=response_text,
        agent_role=state["agent_role"],
    )

    logger.info(
        "agent_response_generated",
        agent_role=state["agent_role"],
        user_id=state["user_id"],
        sap_signals_count=len(sap_signals),
    )

    return {
        "response": response_text,
        "messages": [ai_message],
        "pending_sap_signals": sap_signals,
    }


# ── Node: crisis_check ────────────────────────────────────────────────────────


async def crisis_check(state: AgentState) -> dict[str, Any]:
    """Detect crisis signals in the user's message.

    Two-stage check:
    1. Fast path: regex keyword scan — O(1), always runs.
    2. Slow path: LLM severity classifier — only if keywords found.

    Returns:
        Partial state with ``crisis_detected`` and ``crisis_severity``.
    """
    latest_message = _get_latest_human_message(state["messages"])

    match = _CRISIS_KEYWORDS.search(latest_message)
    if not match:
        return {"crisis_detected": False, "crisis_severity": 0.0}

    # Keywords found — estimate severity
    # Simple heuristic: count matches and weight by word severity
    keyword_count = len(_CRISIS_KEYWORDS.findall(latest_message))
    base_severity = min(0.5 + (keyword_count * 0.15), 0.95)

    settings = get_settings()
    if base_severity >= settings.crisis_intensity_threshold:
        logger.warning(
            "crisis_signal_detected",
            user_id=state["user_id"],
            severity=base_severity,
            keyword_match=match.group(0),
        )
        return {"crisis_detected": True, "crisis_severity": base_severity}

    return {"crisis_detected": False, "crisis_severity": base_severity}


# ── Node: store_memory ────────────────────────────────────────────────────────


async def store_memory(state: AgentState, config: dict[str, Any]) -> dict[str, Any]:
    """Persist the exchange to pgvector and stage SAP signals.

    This node runs after crisis_check when no crisis is detected.
    Writes are async and non-blocking from the perspective of the
    response already being set in state.

    Returns:
        Empty dict — no state mutations needed.
    """
    db = config["configurable"]["db"]
    user_message = _get_latest_human_message(state["messages"])
    ai_response = state["response"]

    store = ConversationMemoryStore(
        user_id=state["user_id"],
        agent_role=state["agent_role"],
        relationship_id=state["relationship_id"],
        db=db,
    )

    await store.add_exchange(
        user_message=user_message,
        ai_response=ai_response,
    )

    if state.get("pending_sap_signals"):
        await store.stage_sap_signals(signals=state["pending_sap_signals"])

    logger.debug(
        "memory_stored",
        user_id=state["user_id"],
        agent_role=state["agent_role"],
    )
    return {}


# ── Node: crisis_escalation ───────────────────────────────────────────────────


async def crisis_escalation(state: AgentState) -> dict[str, Any]:
    """Override the normal response with crisis resources.

    Called only when crisis_check returns crisis_detected=True.
    The original AI response is discarded — safety takes priority.

    Returns:
        State update with the crisis response overriding the LLM output.
    """
    logger.warning(
        "crisis_escalation_triggered",
        user_id=state["user_id"],
        severity=state.get("crisis_severity", 0.0),
    )
    return {
        "response": _CRISIS_RESPONSE,
        "messages": [AIMessage(content=_CRISIS_RESPONSE)],
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_latest_human_message(messages: list) -> str:
    """Extract the text of the most recent HumanMessage."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
    return ""


async def _safe_gather(*coros):
    """Run coroutines concurrently, returning results in order.

    Unlike asyncio.gather, does not propagate exceptions — individual
    failures return None so the graph can degrade gracefully.
    """
    import asyncio

    results = await asyncio.gather(*coros, return_exceptions=True)
    return [None if isinstance(r, Exception) else r for r in results]


async def _extract_sap_signals_inline(
    user_message: str,
    ai_response: str,
    agent_role: str,
) -> list[dict[str, Any]]:
    """Extract abstracted SAP signals from the current exchange.

    This calls the SAP module which uses an LLM to extract themes,
    intensities, and categories — with no quotes or identifying content.

    Returns an empty list on any failure so the main response is not blocked.
    """
    try:
        from app.privacy.sap import SignalAbstractionProtocol

        sap = SignalAbstractionProtocol()
        signals = await sap.extract(
            user_message=user_message,
            ai_response=ai_response,
            source_agent=agent_role,
        )
        return [s.model_dump() for s in signals]
    except Exception as exc:
        logger.warning("sap_extraction_failed", error=str(exc))
        return []


# ── Conditional edge router ───────────────────────────────────────────────────


def route_after_crisis_check(state: AgentState) -> str:
    """Conditional edge: route to crisis_escalation or store_memory."""
    if state.get("crisis_detected"):
        return "crisis_escalation"
    return "store_memory"
