"""Agent B API endpoints — Partner B's private counseling session.

Structurally identical to agent_a.py. Enforces partner_tag="partner_b".
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy import text

from app.agents.agent_b import agent_b_graph
from app.core.exceptions import TrinityError
from app.core.logging import get_logger
from app.deps import CurrentUser, DBSession

router = APIRouter(prefix="/agent-b", tags=["Agent B"])
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    message: str
    partner_name: str | None = None


class ChatResponse(BaseModel):
    response: str
    crisis_detected: bool = False


@router.post("/chat", response_model=ChatResponse)
async def agent_b_chat(
    body: ChatRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ChatResponse:
    """Send a message to Agent B (Partner B's private counselor).

    JWT must contain partner_tag="partner_b". Agent B's memory namespace
    is fully isolated from Agent A.
    """
    if current_user.partner_tag != "partner_b":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for Partner B only.",
        )

    initial_state = {
        "messages": [HumanMessage(content=body.message)],
        "user_id": current_user.sub,
        "partner_id": "",
        "relationship_id": current_user.relationship_id,
        "agent_role": "agent_b",
        "partner_name": body.partner_name or "you",
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }

    config = {"configurable": {"db": db}}

    try:
        final_state = await agent_b_graph.ainvoke(initial_state, config=config)
    except TrinityError:
        raise
    except Exception as exc:
        logger.error("agent_b_invoke_failed", user_id=current_user.sub, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent B encountered an error. Please try again.",
        ) from exc

    return ChatResponse(
        response=final_state["response"],
        crisis_detected=final_state.get("crisis_detected", False),
    )


@router.get("/history")
async def agent_b_history(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 20,
) -> dict:
    """Retrieve Partner B's session history."""
    if current_user.partner_tag != "partner_b":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for Partner B only.",
        )

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
            "namespace": f"agent_b:{current_user.relationship_id}",
            "limit": limit,
        },
    )
    rows = result.fetchall()
    return {
        "exchanges": [{"content": r[0], "metadata": r[1], "created_at": str(r[2])} for r in rows],
        "total": len(rows),
    }
