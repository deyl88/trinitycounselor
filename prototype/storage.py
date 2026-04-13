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
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("America/Los_Angeles")


def _now() -> str:
    return datetime.now(_TZ).isoformat()


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

            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id  TEXT UNIQUE NOT NULL,
                email      TEXT NOT NULL,
                name       TEXT NOT NULL,
                picture    TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code TEXT NOT NULL,
                partner_role TEXT NOT NULL,
                role         TEXT NOT NULL,
                content      TEXT NOT NULL,
                created_at   TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages (session_code, partner_role, created_at);

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
            (code, partner_a_name, partner_b_name, _now())
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
    now = _now()

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


# ── Full message log (exhaustive history) ────────────────────────────────────

def log_message(session_code: str, partner_role: str, role: str, content: str):
    """Append a single message to the permanent log. Never deleted."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (session_code, partner_role, role, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_code, partner_role, role, content, _now())
        )


def get_full_history(session_code: str, partner_role: str) -> list[dict]:
    """Return every message ever sent in this session for this partner."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages "
            "WHERE session_code = ? AND partner_role = ? ORDER BY created_at ASC",
            (session_code, partner_role)
        ).fetchall()
        return [dict(r) for r in rows]


# ── User accounts ─────────────────────────────────────────────────────────────

def create_or_update_user(google_id: str, email: str, name: str, picture: str = "") -> int:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO users (google_id, email, name, picture, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (google_id) DO UPDATE SET
                   email = excluded.email,
                   name  = excluded.name,
                   picture = excluded.picture""",
            (google_id, email, name, picture, _now())
        )
        row = conn.execute("SELECT id FROM users WHERE google_id = ?", (google_id,)).fetchone()
        return row["id"]


def create_user_session(user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    expires_at = (datetime.now(_TZ) + timedelta(days=30)).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO user_sessions (session_id, user_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, user_id, _now(), expires_at)
        )
    return session_id


def get_user_by_session(session_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """SELECT u.id, u.email, u.name, u.picture
               FROM user_sessions s
               JOIN users u ON u.id = s.user_id
               WHERE s.session_id = ? AND s.expires_at > ?""",
            (session_id, _now())
        ).fetchone()
        return dict(row) if row else None


def delete_user_session(session_id: str):
    with _connect() as conn:
        conn.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))


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
