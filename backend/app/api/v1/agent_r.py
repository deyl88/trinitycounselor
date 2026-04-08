"""Agent R API endpoints — Relationship Counselor sessions.

Agent R handles two session types:
  1. Guided (/chat) — one partner consulting the relationship lens
  2. Joint (/joint) — both partners in a mediated session

Both endpoints use the agent_r_graph which enriches context from the RKG
before generating a response.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.agents.agent_r import agent_r_graph
from app.core.exceptions import TrinityError
from app.core.logging import get_logger
from app.deps import CurrentUser, DBSession

router = APIRouter(prefix="/agent-r", tags=["Agent R"])
logger = get_logger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────


class GuidedChatRequest(BaseModel):
    message: str
    partner_name: str | None = None


class JointMessage(BaseModel):
    partner_tag: str = Field(pattern="^partner_[ab]$")
    message: str
    partner_name: str | None = None


class JointSessionRequest(BaseModel):
    """Both partners' messages for a joint session turn."""
    partner_a_message: str | None = None
    partner_b_message: str | None = None
    # In practice one partner speaks at a time in joint session;
    # both fields allow pre-loaded context or simultaneous check-in.


class AgentRResponse(BaseModel):
    response: str
    crisis_detected: bool = False
    session_mode: str  # "guided" | "joint"


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=AgentRResponse)
async def agent_r_guided_chat(
    body: GuidedChatRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> AgentRResponse:
    """Guided session — one partner consulting with the Relationship Counselor.

    The counselor has access to the relational model (RKG) but NOT to
    either partner's private history. Context is relational-level only.

    Available to both partner_a and partner_b.
    """
    initial_state = {
        "messages": [HumanMessage(content=body.message)],
        "user_id": current_user.sub,
        "partner_id": "",
        "relationship_id": current_user.relationship_id,
        "agent_role": "agent_r",
        "partner_name": body.partner_name or current_user.partner_tag,
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }

    config = {"configurable": {"db": db}}

    try:
        final_state = await agent_r_graph.ainvoke(initial_state, config=config)
    except TrinityError:
        raise
    except Exception as exc:
        logger.error("agent_r_guided_failed", user_id=current_user.sub, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Relationship Agent encountered an error.",
        ) from exc

    return AgentRResponse(
        response=final_state["response"],
        crisis_detected=final_state.get("crisis_detected", False),
        session_mode="guided",
    )


@router.post("/joint", response_model=AgentRResponse)
async def agent_r_joint_session(
    body: JointSessionRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> AgentRResponse:
    """Joint mediated session — both partners present with the Relationship Counselor.

    In a joint session, Agent R sees both partners' current messages
    (provided in the request) but still has NO access to their private histories.
    It mediates from the relational model and the current joint session context.

    Typically called by the partner who just spoke; the other partner's message
    may be empty or pre-loaded from the session UI.
    """
    # Compose a joint message incorporating whichever partner(s) spoke
    parts = []
    if body.partner_a_message:
        parts.append(f"[Partner A]: {body.partner_a_message}")
    if body.partner_b_message:
        parts.append(f"[Partner B]: {body.partner_b_message}")

    if not parts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one partner message is required.",
        )

    combined_message = "\n".join(parts)

    initial_state = {
        "messages": [HumanMessage(content=combined_message)],
        "user_id": current_user.sub,
        "partner_id": "",
        "relationship_id": current_user.relationship_id,
        "agent_role": "agent_r",
        "partner_name": "both partners",
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }

    config = {"configurable": {"db": db}}

    try:
        final_state = await agent_r_graph.ainvoke(initial_state, config=config)
    except TrinityError:
        raise
    except Exception as exc:
        logger.error("agent_r_joint_failed", relationship_id=current_user.relationship_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Joint session encountered an error.",
        ) from exc

    return AgentRResponse(
        response=final_state["response"],
        crisis_detected=final_state.get("crisis_detected", False),
        session_mode="joint",
    )
