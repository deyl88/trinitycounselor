import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from tiktok import get_auth_url, exchange_code
from database import get_db

router = APIRouter()

TIKTOK_REDIRECT_URI = os.getenv(
    "TIKTOK_REDIRECT_URI", "http://localhost:8000/api/auth/tiktok/callback"
)


@router.get("/tiktok/start")
def tiktok_start():
    """Redirect user to TikTok OAuth consent screen."""
    url = get_auth_url(redirect_uri=TIKTOK_REDIRECT_URI)
    return RedirectResponse(url)


@router.get("/tiktok/callback")
def tiktok_callback(code: str = None, error: str = None, state: str = None):
    """TikTok redirects here after user grants access."""
    if error or not code:
        raise HTTPException(400, f"TikTok auth denied: {error or 'no code returned'}")

    token_data = exchange_code(code, TIKTOK_REDIRECT_URI)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(500, f"Token exchange failed: {token_data}")

    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("tiktok_access_token", access_token),
        )
        if token_data.get("refresh_token"):
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("tiktok_refresh_token", token_data["refresh_token"]),
            )

    return {"status": "connected", "platform": "tiktok"}


@router.get("/tiktok/status")
def tiktok_status():
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key='tiktok_access_token'"
        ).fetchone()
    return {"connected": row is not None}
