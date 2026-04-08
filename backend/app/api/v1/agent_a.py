"""Agent A API endpoints — Partner A's private counseling session.

All endpoints here require authentication. The JWT's partner_tag must
be "partner_a" — enforced in the invoke helper. This prevents Partner B
from sending messages to Agent A's namespace.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_a import agent_a_graph
from app.core.exceptions import TrinityError
from app.core.logging import get_logger
from app.deps import CurrentUser, DBSession

router = APIRouter(prefix="/agent-a", tags=["Agent A"])
logger = get_logger(__name__)


# ── Request / Response schemas ────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    partner_name: str | None = None  # Display name, injected into system prompt


class ChatResponse(BaseModel):
    response: str
    crisis_detected: bool = False
    session_id: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def agent_a_chat(
    body: ChatRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ChatResponse:
    """Send a message to Agent A (Partner A's private counselor).

    This endpoint is exclusively for Partner A. The JWT must contain
    partner_tag="partner_a". Agent A's memory namespace is fully isolated
    from Agent B — there is no path for private content to cross.

    Returns the counselor's response and a crisis_detected flag.
    If crisis_detected is True, the response contains crisis resources
    and the normal counseling response has been suppressed.
    """
    if current_user.partner_tag != "partner_a":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for Partner A only.",
        )

    partner_name = body.partner_name or "you"

    initial_state = {
        "messages": [HumanMessage(content=body.message)],
        "user_id": current_user.sub,
        "partner_id": "",  # Not needed for solo session
        "relationship_id": current_user.relationship_id,
        "agent_role": "agent_a",
        "partner_name": partner_name,
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }

    config = {"configurable": {"db": db}}

    try:
        final_state = await agent_a_graph.ainvoke(initial_state, config=config)
    except TrinityError:
        raise
    except Exception as exc:
        logger.error("agent_a_invoke_failed", user_id=current_user.sub, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent A encountered an error. Please try again.",
        ) from exc

    return ChatResponse(
        response=final_state["response"],
        crisis_detected=final_state.get("crisis_detected", False),
    )


@router.get("/history")
async def agent_a_history(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 20,
) -> dict:
    """Retrieve Partner A's session history (most recent exchanges).

    Returns paginated conversation history from pgvector for the
    authenticated user's Agent A namespace.

    TODO: Implement pagination and filtering.
    """
    if current_user.partner_tag != "partner_a":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for Partner A only.",
        )

    from sqlalchemy import text

    result = await db.execute(
        text(
            "SELECT content, metadata, created_at "
            "FROM conversation_memory "
            "WHERE user_id = :user_id "
            "AND namespace = :namespace "
            "ORDER BY created_at DESC "
            "LIMIT :limit"
        ),
        {
            "user_id": current_user.sub,
            "namespace": f"agent_a:{current_user.relationship_id}",
            "limit": limit,
        },
    )
    rows = result.fetchall()

    return {
        "exchanges": [
            {"content": r[0], "metadata": r[1], "created_at": str(r[2])}
            for r in rows
        ],
        "total": len(rows),
    }
