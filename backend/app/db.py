"""SQLite data layer for wolio.ai — single-file, zero-config."""
import sqlite3
import json
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "wolio.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    age_group     TEXT,
    grade         TEXT,
    language      TEXT DEFAULT 'hinglish',
    tone          TEXT DEFAULT 'fun',
    voice         INTEGER DEFAULT 1,
    avatar        TEXT,                      -- JSON
    interests     TEXT,                      -- JSON array
    learning_style TEXT,                     -- games | stories | quizzes
    difficulty_tier INTEGER DEFAULT 1,
    xp            INTEGER DEFAULT 0,
    streak        INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now')),
    onboarded     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS concepts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    subject       TEXT,
    world         TEXT,                      -- which learning world
    learned_via   TEXT,                      -- 'Space Game Mission' etc.
    difficulty    TEXT DEFAULT 'beginner',
    mastery       INTEGER DEFAULT 20,        -- 0-100
    memory_strength INTEGER DEFAULT 100,     -- decays over time
    emoji         TEXT DEFAULT '✨',
    summary       TEXT,
    learned_at    TEXT DEFAULT (datetime('now')),
    last_revised  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind          TEXT,                      -- onboarding_task, mission, revision...
    payload       TEXT,                      -- JSON
    created_at    TEXT DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def jdump(value: Any) -> Optional[str]:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def jload(value: Optional[str], default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
