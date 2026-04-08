"""
Trinity persistent storage using SQLite.

All conversation history, therapeutic summaries, and relational models
are saved here after every message. Loads automatically on startup.

The database file location is set by the DB_PATH environment variable.
Default: ./data/trinity.db

On Railway: set DB_PATH to a path inside a mounted Volume, e.g. /data/trinity.db
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


def _db_path() -> str:
    path = os.environ.get("DB_PATH", str(Path(__file__).parent / "data" / "trinity.db"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                code            TEXT PRIMARY KEY,
                partner_a_name  TEXT NOT NULL,
                partner_b_name  TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_state (
                code                    TEXT NOT NULL,
                agent_role              TEXT NOT NULL,   -- 'a', 'b', 'r'
                conversation_history    TEXT NOT NULL DEFAULT '[]',
                therapeutic_summary     TEXT NOT NULL DEFAULT '',
                recent_messages_buffer  TEXT NOT NULL DEFAULT '[]',
                relational_model        TEXT NOT NULL DEFAULT '',
                active_themes           TEXT NOT NULL DEFAULT '[]',
                updated_at              TEXT NOT NULL,
                PRIMARY KEY (code, agent_role)
            );
        """)


# ── Session CRUD ──────────────────────────────────────────────────────────────

def save_session(code: str, partner_a_name: str, partner_b_name: str):
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (code, partner_a_name, partner_b_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (code, partner_a_name, partner_b_name, datetime.utcnow().isoformat())
        )


def load_all_sessions() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM sessions").fetchall()
        return [dict(r) for r in rows]


def session_exists(code: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM sessions WHERE code = ?", (code,)).fetchone()
        return row is not None


def get_session_meta(code: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE code = ?", (code,)).fetchone()
        return dict(row) if row else None


# ── Agent state CRUD ──────────────────────────────────────────────────────────

def save_agent_state(code: str, agent_role: str, agent):
    """Persist a PartnerAgent or RelationshipCounselor to the DB."""
    now = datetime.utcnow().isoformat()

    if agent_role in ("a", "b"):
        # PartnerAgent
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_state
                    (code, agent_role, conversation_history, therapeutic_summary,
                     recent_messages_buffer, relational_model, active_themes, updated_at)
                VALUES (?, ?, ?, ?, ?, '', '[]', ?)
                ON CONFLICT (code, agent_role) DO UPDATE SET
                    conversation_history   = excluded.conversation_history,
                    therapeutic_summary    = excluded.therapeutic_summary,
                    recent_messages_buffer = excluded.recent_messages_buffer,
                    updated_at             = excluded.updated_at
                """,
                (
                    code,
                    agent_role,
                    json.dumps(agent.conversation_history),
                    agent.therapeutic_summary,
                    json.dumps(agent.recent_messages_buffer),
                    now,
                )
            )
    else:
        # RelationshipCounselor (role = 'r')
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_state
                    (code, agent_role, conversation_history, therapeutic_summary,
                     recent_messages_buffer, relational_model, active_themes, updated_at)
                VALUES (?, ?, ?, '', '[]', ?, ?, ?)
                ON CONFLICT (code, agent_role) DO UPDATE SET
                    conversation_history = excluded.conversation_history,
                    relational_model     = excluded.relational_model,
                    active_themes        = excluded.active_themes,
                    updated_at           = excluded.updated_at
                """,
                (
                    code,
                    agent_role,
                    json.dumps(agent.conversation_history),
                    agent.relational_model,
                    json.dumps(agent.active_themes),
                    now,
                )
            )


def load_agent_state(code: str, agent_role: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM agent_state WHERE code = ? AND agent_role = ?",
            (code, agent_role)
        ).fetchone()
        if not row:
            return None
        return {
            "conversation_history":   json.loads(row["conversation_history"]),
            "therapeutic_summary":    row["therapeutic_summary"],
            "recent_messages_buffer": json.loads(row["recent_messages_buffer"]),
            "relational_model":       row["relational_model"],
            "active_themes":          json.loads(row["active_themes"]),
        }
