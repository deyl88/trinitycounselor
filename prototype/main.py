"""
Trinity Counselor — FastAPI Application (with Web UI)
"""

import os
import random
import string
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import TrinitySystem

app = FastAPI(title="Trinity Counselor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ───────────────────────────────────────────────────
sessions: dict[str, TrinitySystem] = {}
session_meta: dict[str, dict] = {}  # stores partner names + codes


def _gen_code() -> str:
    """Generate a short memorable session code like RIVER4."""
    words = ["CALM", "TIDE", "LAKE", "MIST", "SAGE", "REED",
             "MOSS", "FERN", "DUSK", "DAWN", "DOVE", "ECHO"]
    return random.choice(words) + str(random.randint(10, 99))


# ── Request Models ────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    partner_a_name: str
    partner_b_name: str


class JoinSessionRequest(BaseModel):
    code: str
    partner: str   # "a" or "b"


class SoloSessionRequest(BaseModel):
    relationship_id: str
    partner: str   # "a" or "b"
    message: str


class JointSessionRequest(BaseModel):
    relationship_id: str
    speaker: str   # "a" or "b"
    message: str


# ── Web UI ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_app():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text())


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/session/create")
def create_session(req: CreateSessionRequest):
    """Partner A creates a new session. Returns a shareable code for Partner B."""
    code = _gen_code()
    while code in sessions:
        code = _gen_code()

    sessions[code] = TrinitySystem(
        partner_a_name=req.partner_a_name,
        partner_b_name=req.partner_b_name,
    )
    session_meta[code] = {
        "partner_a_name": req.partner_a_name,
        "partner_b_name": req.partner_b_name,
    }
    return {
        "code": code,
        "partner_a_name": req.partner_a_name,
        "partner_b_name": req.partner_b_name,
    }


@app.get("/api/session/{code}")
def get_session(code: str):
    """Look up a session by code — used when Partner B joins."""
    code = code.upper()
    if code not in sessions:
        raise HTTPException(404, "Session not found. Check your code.")
    meta = session_meta[code]
    return {
        "code": code,
        "partner_a_name": meta["partner_a_name"],
        "partner_b_name": meta["partner_b_name"],
    }


@app.post("/api/solo")
async def solo_session(req: SoloSessionRequest):
    """Private session with one partner's counselor."""
    trinity = _get_trinity(req.relationship_id)
    response = trinity.solo_session(req.partner, req.message)
    return {"response": response}


@app.post("/api/sync")
async def sync_ril(relationship_id: str):
    """Sync private sessions into the relational model."""
    trinity = _get_trinity(relationship_id)
    trinity.sync_to_ril()
    return {"status": "synced"}


@app.post("/api/joint")
async def joint_session(req: JointSessionRequest):
    """Joint session mediated by the Relationship Counselor."""
    trinity = _get_trinity(req.relationship_id)
    response = trinity.joint_session(req.speaker, req.message)
    return {"response": response}


@app.get("/api/model/{relationship_id}")
def get_model(relationship_id: str):
    trinity = _get_trinity(relationship_id)
    return {
        "relational_model": trinity.relationship_counselor.relational_model,
        "active_themes": trinity.relationship_counselor.active_themes,
    }


# Legacy endpoints (keep for compatibility with demo.py)
@app.post("/relationships")
def create_relationship_legacy(req: dict):
    rel_id = req.get("relationship_id", _gen_code())
    if rel_id not in sessions:
        sessions[rel_id] = TrinitySystem(
            partner_a_name=req.get("partner_a_name", "Partner A"),
            partner_b_name=req.get("partner_b_name", "Partner B"),
        )
        session_meta[rel_id] = {
            "partner_a_name": req.get("partner_a_name", "Partner A"),
            "partner_b_name": req.get("partner_b_name", "Partner B"),
        }
    return {"status": "ok", "relationship_id": rel_id}

@app.post("/solo")
def solo_legacy(req: SoloSessionRequest):
    return {"response": _get_trinity(req.relationship_id).solo_session(req.partner, req.message)}

@app.post("/sync")
def sync_legacy(relationship_id: str):
    _get_trinity(relationship_id).sync_to_ril()
    return {"status": "synced"}

@app.post("/joint")
def joint_legacy(req: JointSessionRequest):
    return {"response": _get_trinity(req.relationship_id).joint_session(req.speaker, req.message)}

@app.get("/model/{relationship_id}")
def model_legacy(relationship_id: str):
    t = _get_trinity(relationship_id)
    return {"relational_model": t.relationship_counselor.relational_model}


def _get_trinity(rel_id: str) -> TrinitySystem:
    if rel_id not in sessions:
        raise HTTPException(404, f"Session '{rel_id}' not found.")
    return sessions[rel_id]


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
