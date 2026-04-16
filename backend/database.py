import sqlite3
import contextlib
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "./sv_studio.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    platform           TEXT    NOT NULL,
    platform_video_id  TEXT    UNIQUE NOT NULL,
    title              TEXT,
    caption            TEXT,
    duration_seconds   INTEGER,
    posted_at          TEXT,
    views              INTEGER DEFAULT 0,
    likes              INTEGER DEFAULT 0,
    comments           INTEGER DEFAULT 0,
    shares             INTEGER DEFAULT 0,
    saves              INTEGER DEFAULT 0,
    follower_gain      INTEGER,
    song_name          TEXT,
    song_artist        TEXT,
    is_cover           INTEGER DEFAULT 0,
    is_original        INTEGER DEFAULT 0,
    enrichment_json    TEXT,
    created_at         TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS style_fingerprint (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    computed_at     TEXT    DEFAULT (datetime('now')),
    fingerprint_json TEXT   NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    song_name        TEXT    NOT NULL,
    song_artist      TEXT,
    trending_score   REAL    DEFAULT 0,
    style_fit_score  REAL    DEFAULT 0,
    final_score      REAL    DEFAULT 0,
    tip_text         TEXT,
    status           TEXT    DEFAULT 'pending',
    generated_at     TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
