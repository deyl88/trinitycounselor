"""
Trinity Counselor — FastAPI Application (with Web UI + Persistence)
"""

import os
import random
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agents import TrinitySystem
import storage

app = FastAPI(title="Trinity Counselor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory cache (loaded from DB on startup) ───────────────────────────────
sessions: dict[str, TrinitySystem] = {}


def _gen_code() -> str:
    words = ["CALM", "TIDE", "LAKE", "MIST", "SAGE", "REED",
             "MOSS", "FERN", "DUSK", "DAWN", "DOVE", "ECHO"]
    return random.choice(words) + str(random.randint(10, 99))


def _save(code: str, trinity: TrinitySystem):
    """Persist all three agents to the DB after any state change."""
    storage.save_agent_state(code, "a", trinity.agent_a)
    storage.save_agent_state(code, "b", trinity.agent_b)
    storage.save_agent_state(code, "r", trinity.relationship_counselor)


def _load_trinity(code: str, partner_a_name: str, partner_b_name: str) -> TrinitySystem:
    """Reconstruct a TrinitySystem from saved DB state."""
    trinity = TrinitySystem(
        partner_a_name=partner_a_name,
        partner_b_name=partner_b_name,
    )
    for role, agent in [("a", trinity.agent_a), ("b", trinity.agent_b)]:
        state = storage.load_agent_state(code, role)
        if state:
            agent.conversation_history    = state["conversation_history"]
            agent.therapeutic_summary     = state["therapeutic_summary"]
            agent.recent_messages_buffer  = state["recent_messages_buffer"]

    state_r = storage.load_agent_state(code, "r")
    if state_r:
        trinity.relationship_counselor.conversation_history = state_r["conversation_history"]
        trinity.relationship_counselor.relational_model     = state_r["relational_model"]
        trinity.relationship_counselor.active_themes        = state_r["active_themes"]

    return trinity


@app.on_event("startup")
def startup():
    """Initialize DB and reload all existing sessions into memory."""
    storage.init_db()
    for row in storage.load_all_sessions():
        code = row["code"]
        sessions[code] = _load_trinity(code, row["partner_a_name"], row["partner_b_name"])
    print(f"[Trinity] Loaded {len(sessions)} session(s) from database.")


# ── Request Models ────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    partner_a_name: str
    partner_b_name: str


class SoloSessionRequest(BaseModel):
    relationship_id: str
    partner: str
    message: str


class JointSessionRequest(BaseModel):
    relationship_id: str
    speaker: str
    message: str


# ── Web UI ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_landing():
    html_path = Path(__file__).parent / "static" / "landing.html"
    return HTMLResponse(content=html_path.read_text())

@app.get("/app", response_class=HTMLResponse)
def serve_app():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text())


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/session/create")
def create_session(req: CreateSessionRequest):
    code = _gen_code()
    while storage.session_exists(code):
        code = _gen_code()

    trinity = TrinitySystem(
        partner_a_name=req.partner_a_name,
        partner_b_name=req.partner_b_name,
    )
    sessions[code] = trinity
    storage.save_session(code, req.partner_a_name, req.partner_b_name)
    _save(code, trinity)

    return {"code": code, "partner_a_name": req.partner_a_name, "partner_b_name": req.partner_b_name}


@app.get("/api/session/{code}")
def get_session(code: str):
    code = code.upper()
    meta = storage.get_session_meta(code)
    if not meta:
        raise HTTPException(404, "Session not found. Check your code.")
    # Reload into memory if it was lost (e.g. after a restart)
    if code not in sessions:
        sessions[code] = _load_trinity(code, meta["partner_a_name"], meta["partner_b_name"])
    return {"code": code, "partner_a_name": meta["partner_a_name"], "partner_b_name": meta["partner_b_name"]}


@app.post("/api/solo")
def solo_session(req: SoloSessionRequest):
    trinity = _get_trinity(req.relationship_id)
    response = trinity.solo_session(req.partner, req.message)
    # Save the agent that just spoke
    agent = trinity.agent_a if req.partner == "a" else trinity.agent_b
    storage.save_agent_state(req.relationship_id, req.partner, agent)
    return {"response": response}


@app.post("/api/sync")
def sync_ril(relationship_id: str):
    trinity = _get_trinity(relationship_id)
    trinity.sync_to_ril()
    _save(relationship_id, trinity)
    return {"status": "synced"}


@app.post("/api/joint")
def joint_session(req: JointSessionRequest):
    trinity = _get_trinity(req.relationship_id)
    response = trinity.joint_session(req.speaker, req.message)
    storage.save_agent_state(req.relationship_id, "r", trinity.relationship_counselor)
    return {"response": response}


@app.get("/api/model/{relationship_id}")
def get_model(relationship_id: str):
    trinity = _get_trinity(relationship_id)
    return {
        "relational_model": trinity.relationship_counselor.relational_model,
        "active_themes": trinity.relationship_counselor.active_themes,
    }


# ── Legacy endpoints (keep demo.py working) ───────────────────────────────────

@app.post("/relationships")
def create_relationship_legacy(req: dict):
    rel_id = req.get("relationship_id", _gen_code())
    if not storage.session_exists(rel_id):
        trinity = TrinitySystem(
            partner_a_name=req.get("partner_a_name", "Partner A"),
            partner_b_name=req.get("partner_b_name", "Partner B"),
        )
        sessions[rel_id] = trinity
        storage.save_session(rel_id, req.get("partner_a_name", "Partner A"), req.get("partner_b_name", "Partner B"))
        _save(rel_id, trinity)
    return {"status": "ok", "relationship_id": rel_id}

@app.post("/solo")
def solo_legacy(req: SoloSessionRequest):
    trinity = _get_trinity(req.relationship_id)
    response = trinity.solo_session(req.partner, req.message)
    agent = trinity.agent_a if req.partner == "a" else trinity.agent_b
    storage.save_agent_state(req.relationship_id, req.partner, agent)
    return {"response": response}

@app.post("/sync")
def sync_legacy(relationship_id: str):
    trinity = _get_trinity(relationship_id)
    trinity.sync_to_ril()
    _save(relationship_id, trinity)
    return {"status": "synced"}

@app.post("/joint")
def joint_legacy(req: JointSessionRequest):
    trinity = _get_trinity(req.relationship_id)
    response = trinity.joint_session(req.speaker, req.message)
    storage.save_agent_state(req.relationship_id, "r", trinity.relationship_counselor)
    return {"response": response}

@app.get("/model/{relationship_id}")
def model_legacy(relationship_id: str):
    t = _get_trinity(relationship_id)
    return {"relational_model": t.relationship_counselor.relational_model}


def _get_trinity(rel_id: str) -> TrinitySystem:
    if rel_id not in sessions:
        # Try reloading from DB (handles restart case)
        meta = storage.get_session_meta(rel_id)
        if meta:
            sessions[rel_id] = _load_trinity(rel_id, meta["partner_a_name"], meta["partner_b_name"])
        else:
            raise HTTPException(404, f"Session '{rel_id}' not found.")
    return sessions[rel_id]


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
