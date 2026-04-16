"""
Trinity Counselor — FastAPI Application

Endpoints for solo sessions, joint sessions, and RIL sync.
"""

import os

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import TrinitySystem

app = FastAPI(title="Trinity Counselor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (replace with DB in production) ───────────────────
# Maps relationship_id -> TrinitySystem
sessions: dict[str, TrinitySystem] = {}


# ── Request Models ────────────────────────────────────────────────────────────

class CreateRelationshipRequest(BaseModel):
    relationship_id: str
    partner_a_name: str
    partner_b_name: str


class SoloSessionRequest(BaseModel):
    relationship_id: str
    partner: str  # "a" or "b"
    message: str


class JointSessionRequest(BaseModel):
    relationship_id: str
    speaker: str  # "a" or "b"
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/relationships")
def create_relationship(req: CreateRelationshipRequest):
    """Initialize a Trinity system for a relationship."""
    if req.relationship_id in sessions:
        raise HTTPException(400, "Relationship already exists")

    sessions[req.relationship_id] = TrinitySystem(
        partner_a_name=req.partner_a_name,
        partner_b_name=req.partner_b_name,
    )
    return {"status": "created", "relationship_id": req.relationship_id}


@app.post("/solo")
def solo_session(req: SoloSessionRequest):
    """
    Private session with one partner's counselor.
    The other partner never sees this conversation.
    """
    trinity = _get_trinity(req.relationship_id)
    try:
        response = trinity.solo_session(req.partner, req.message)
    except anthropic.APITimeoutError:
        raise HTTPException(503, "AI service timed out. Please try again.")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Unable to reach AI service. Please try again.")
    except anthropic.InternalServerError:
        raise HTTPException(503, "AI service error. Please try again shortly.")
    except anthropic.APIError as exc:
        raise HTTPException(502, f"AI service returned an error: {exc.message}")
    return {"response": response, "mode": "private"}


@app.post("/sync")
def sync_ril(relationship_id: str):
    """
    Trigger RIL sync — extract abstracted signals from both private
    agents and update the Relationship Counselor's model.
    Call this after a batch of solo sessions.
    """
    trinity = _get_trinity(relationship_id)
    try:
        trinity.sync_to_ril()
    except anthropic.APITimeoutError:
        raise HTTPException(503, "AI service timed out during sync. Please try again.")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Unable to reach AI service. Please try again.")
    except anthropic.InternalServerError:
        raise HTTPException(503, "AI service error during sync. Please try again shortly.")
    except anthropic.APIError as exc:
        raise HTTPException(502, f"AI service returned an error: {exc.message}")
    return {
        "status": "synced",
        "relational_model": trinity.relationship_counselor.relational_model,
        "active_themes_count": len(trinity.relationship_counselor.active_themes),
    }


@app.post("/joint")
def joint_session(req: JointSessionRequest):
    """
    Joint session mediated by the Relationship Counselor.
    Operates only from abstracted relational context — no private data.
    """
    trinity = _get_trinity(req.relationship_id)
    try:
        response = trinity.joint_session(req.speaker, req.message)
    except anthropic.APITimeoutError:
        raise HTTPException(503, "AI service timed out. Please try again.")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Unable to reach AI service. Please try again.")
    except anthropic.InternalServerError:
        raise HTTPException(503, "AI service error. Please try again shortly.")
    except anthropic.APIError as exc:
        raise HTTPException(502, f"AI service returned an error: {exc.message}")
    return {"response": response, "mode": "joint"}


@app.get("/model/{relationship_id}")
def get_relational_model(relationship_id: str):
    """Inspect the current relational model (for development/debugging)."""
    trinity = _get_trinity(relationship_id)
    return {
        "relational_model": trinity.relationship_counselor.relational_model,
        "active_themes": trinity.relationship_counselor.active_themes,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_trinity(relationship_id: str) -> TrinitySystem:
    if relationship_id not in sessions:
        raise HTTPException(404, f"Relationship '{relationship_id}' not found")
    return sessions[relationship_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
