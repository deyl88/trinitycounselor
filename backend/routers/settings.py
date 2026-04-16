from fastapi import APIRouter, HTTPException
from database import get_db
from models import SettingUpsert, SettingResponse
from typing import List

router = APIRouter()


@router.get("/", response_model=List[SettingResponse])
def list_settings():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM settings").fetchall()
        return [dict(r) for r in rows]


@router.get("/{key}", response_model=SettingResponse)
def get_setting(key: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM settings WHERE key=?", (key,)).fetchone()
        if not row:
            raise HTTPException(404, f"Setting '{key}' not found")
        return dict(row)


@router.put("/", response_model=SettingResponse)
def upsert_setting(setting: SettingUpsert):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
            (setting.key, setting.value),
        )
        row = conn.execute(
            "SELECT * FROM settings WHERE key=?", (setting.key,)
        ).fetchone()
        return dict(row)


# OAuth callback stubs — wired up in a future step
@router.get("/auth/tiktok/callback")
def tiktok_callback(code: str = None):
    return {"status": "stub", "platform": "tiktok", "code_received": code is not None}


@router.get("/auth/instagram/callback")
def instagram_callback(code: str = None):
    return {"status": "stub", "platform": "instagram", "code_received": code is not None}
