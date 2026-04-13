"""
Trinity Counselor — FastAPI Application (with Web UI + Persistence)
"""

import os
import random
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel

from agents import TrinitySystem
import storage

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-please-set-in-prod")

app = FastAPI(title="Trinity Counselor", version="0.1.0")

# Serve static assets (icon, og image, etc.)
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Google OAuth ──────────────────────────────────────────────────────────────
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.get("/auth/google")
async def auth_google(request: Request):
    # Force https — Railway terminates TLS at the proxy level
    redirect_uri = str(request.url_for("auth_google_callback")).replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback", name="auth_google_callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        user_id = storage.create_or_update_user(
            google_id=user_info["sub"],
            email=user_info["email"],
            name=user_info.get("name", ""),
            picture=user_info.get("picture", ""),
        )
        session_id = storage.create_user_session(user_id)
        response = RedirectResponse(url="/app")
        response.set_cookie(
            "trinity_session", session_id,
            httponly=True, secure=True, samesite="lax",
            max_age=30 * 24 * 3600,
        )
        return response
    except Exception:
        return RedirectResponse(url="/?auth_error=1")


@app.get("/auth/logout")
async def logout(request: Request):
    session_id = request.cookies.get("trinity_session")
    if session_id:
        storage.delete_user_session(session_id)
    response = RedirectResponse(url="/")
    response.delete_cookie("trinity_session")
    return response


@app.get("/api/me")
async def get_me(request: Request):
    session_id = request.cookies.get("trinity_session")
    if not session_id:
        raise HTTPException(401, "Not authenticated")
    user = storage.get_user_by_session(session_id)
    if not user:
        raise HTTPException(401, "Session expired")
    return user

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

@app.get("/join/{code}", response_class=HTMLResponse)
def serve_join(code: str):
    # Serves the app — JS detects /join/{code} and pre-fills the join form
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
    agent = trinity.agent_a if req.partner == "a" else trinity.agent_b
    full_text: list[str] = []

    def generate():
        try:
            for chunk in agent.stream_respond(req.message):
                full_text.append(chunk)
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return
        full_response = "".join(full_text)
        storage.save_agent_state(req.relationship_id, req.partner, agent)
        storage.log_message(req.relationship_id, req.partner, "user", req.message)
        storage.log_message(req.relationship_id, req.partner, "assistant", full_response)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/sync")
def sync_ril(relationship_id: str):
    trinity = _get_trinity(relationship_id)
    trinity.sync_to_ril()
    _save(relationship_id, trinity)
    return {"status": "synced"}


@app.post("/api/joint")
def joint_session(req: JointSessionRequest):
    trinity = _get_trinity(req.relationship_id)
    speaker_name = trinity.partner_a_name if req.speaker == "a" else trinity.partner_b_name
    full_text: list[str] = []

    def generate():
        try:
            for chunk in trinity.relationship_counselor.stream_respond(speaker_name, req.message):
                full_text.append(chunk)
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return
        full_response = "".join(full_text)
        storage.save_agent_state(req.relationship_id, "r", trinity.relationship_counselor)
        storage.log_message(req.relationship_id, f"joint_{req.speaker}", "user", req.message)
        storage.log_message(req.relationship_id, f"joint_{req.speaker}", "assistant", full_response)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/session/{code}/history/{partner}")
def get_history(code: str, partner: str):
    if partner not in ("a", "b", "r"):
        raise HTTPException(400, "Partner must be 'a', 'b', or 'r'")
    # Use full permanent log if available, fall back to compressed agent state
    full = storage.get_full_history(code.upper(), partner)
    if full:
        return {"code": code.upper(), "partner": partner, "messages": full}
    state = storage.load_agent_state(code.upper(), partner)
    messages = state["conversation_history"] if state else []
    return {"code": code.upper(), "partner": partner, "messages": messages}


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
