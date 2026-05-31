"""SQLite data layer for wolio.ai — single-file, zero-config."""
import os
import sqlite3
import json
from pathlib import Path
from typing import Any, Optional

# Path is overridable via WOLIO_DB so tests (and staging) use an isolated file.
DB_PATH = Path(os.getenv("WOLIO_DB", Path(__file__).resolve().parent.parent / "wolio.db"))


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

CREATE TABLE IF NOT EXISTS daily_quests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day           TEXT NOT NULL,             -- YYYY-MM-DD (local-ish, server date)
    task_id       TEXT NOT NULL,             -- learn | play | revise
    icon          TEXT,
    label         TEXT,
    target        INTEGER DEFAULT 1,
    reward        INTEGER DEFAULT 20,
    claimed       INTEGER DEFAULT 0,         -- XP already granted?
    UNIQUE(user_id, day, task_id)
);

CREATE TABLE IF NOT EXISTS revision_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id    INTEGER,
    mode          TEXT,                      -- quick | smart | full | challenge
    count         INTEGER DEFAULT 1,         -- concepts touched in the session
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ledger (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind          TEXT,                      -- xp | coin
    amount        INTEGER,                   -- +earn / -spend
    reason        TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS achievements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id      TEXT,
    unlocked_at   TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, badge_id)
);

CREATE TABLE IF NOT EXISTS parents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pin           TEXT DEFAULT '1234',
    plan          TEXT DEFAULT 'free',       -- free | premium | premium_plus
    created_at    TEXT DEFAULT (datetime('now'))
);
"""

# Columns added after the first release. SQLite's CREATE TABLE IF NOT EXISTS
# won't touch an existing table, so we add them defensively at startup.
_USER_MIGRATIONS = {
    "last_world":     "TEXT",
    "last_mission":   "TEXT",
    "last_progress":  "INTEGER DEFAULT 0",
    "coins":          "INTEGER DEFAULT 0",
    "longest_streak": "INTEGER DEFAULT 0",
    "last_active":    "TEXT",
    "unlocked":       "TEXT",      # JSON list of owned shop item ids
    "parent_id":      "INTEGER",   # which parent account owns this child
    "goal_daily_min": "INTEGER DEFAULT 20",
    "goal_subject":   "TEXT",      # subject the parent wants to focus on
    "screen_limit_min": "INTEGER DEFAULT 60",
    "restricted_topics": "TEXT",   # JSON list of topics the parent turned off
}

_CONCEPT_MIGRATIONS = {
    "revision_count": "INTEGER DEFAULT 0",
    "method":         "TEXT",      # JSON list: ["story","game","quiz"]
    "keywords":       "TEXT",      # space-separated search terms
}

_PARENT_MIGRATIONS = {
    "status":       "TEXT DEFAULT 'active'",   # active | trialing | cancelled
    "trial_ends":   "TEXT",
    "renewal_date": "TEXT",
}


def _migrate(conn: sqlite3.Connection) -> None:
    for table, migrations in (("users", _USER_MIGRATIONS),
                              ("concepts", _CONCEPT_MIGRATIONS),
                              ("parents", _PARENT_MIGRATIONS)):
        cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, decl in migrations.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
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
