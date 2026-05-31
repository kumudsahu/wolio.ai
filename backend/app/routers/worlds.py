from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..db import get_conn, jload
from ..brain import WORLDS, rank_worlds

router = APIRouter(prefix="/api", tags=["worlds"])


@router.get("/worlds")
def list_worlds(user_id: Optional[int] = None):
    interests = []
    if user_id:
        conn = get_conn()
        try:
            row = conn.execute("SELECT interests FROM users WHERE id=?", (user_id,)).fetchone()
            if row:
                interests = jload(row["interests"], [])
        finally:
            conn.close()
    return {"worlds": rank_worlds(interests) if interests else WORLDS}


class CompleteMissionIn(BaseModel):
    user_id: int
    world_id: str
    mission_id: str


@router.post("/missions/complete")
def complete_mission(data: CompleteMissionIn):
    """Completing a mission = earning XP + auto-saving the concept to the timeline."""
    world = next((w for w in WORLDS if w["id"] == data.world_id), None)
    if not world:
        raise HTTPException(404, "World not found")
    mission = next((m for m in world["missions"] if m["id"] == data.mission_id), None)
    if not mission:
        raise HTTPException(404, "Mission not found")

    conn = get_conn()
    try:
        user = conn.execute("SELECT * FROM users WHERE id=?", (data.user_id,)).fetchone()
        if not user:
            raise HTTPException(404, "User not found")

        # Auto-save concept to the Life Learning Timeline (or bump mastery if seen).
        existing = conn.execute(
            "SELECT id, mastery FROM concepts WHERE user_id=? AND title=?",
            (data.user_id, mission["concept"]),
        ).fetchone()
        if existing:
            new_mastery = min(100, existing["mastery"] + 25)
            conn.execute(
                "UPDATE concepts SET mastery=?, memory_strength=100, last_revised=datetime('now') WHERE id=?",
                (new_mastery, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO concepts
                   (user_id, title, subject, world, learned_via, difficulty, mastery, emoji, summary)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (data.user_id, mission["concept"], world["subject"], world["name"],
                 f"{world['name']} Mission", "beginner", 35, mission["emoji"],
                 f"Learned during “{mission['title']}”."),
            )
        xp = user["xp"] + 50
        conn.execute("UPDATE users SET xp=? WHERE id=?", (xp, data.user_id))
        conn.execute(
            "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
            (data.user_id, "mission", f'{{"world":"{data.world_id}","mission":"{data.mission_id}"}}'),
        )
        conn.commit()
    finally:
        conn.close()

    return {"xp_earned": 50, "concept_saved": mission["concept"], "emoji": mission["emoji"]}
