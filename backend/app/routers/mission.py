"""Mission API — serves a mission's playbook and records performance.

GET  /api/mission/{world_id}/{mission_id}  → full playbook + current mastery/level
POST /api/mission/finish                   → score the run, update mastery, save concept
"""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..db import get_conn
from ..brain import WORLDS
from ..content import get_playbook, level_label, level_index, make_keywords
from .. import economy

router = APIRouter(prefix="/api", tags=["mission"])


def _find(world_id: str, mission_id: str):
    world = next((w for w in WORLDS if w["id"] == world_id), None)
    if not world:
        raise HTTPException(404, "World not found")
    mission = next((m for m in world["missions"] if m["id"] == mission_id), None)
    if not mission:
        raise HTTPException(404, "Mission not found")
    return world, mission


@router.get("/mission/{world_id}/{mission_id}")
def get_mission(world_id: str, mission_id: str, user_id: Optional[int] = None):
    world, mission = _find(world_id, mission_id)
    playbook = get_playbook(world_id, mission)

    mastery = 0
    conn = get_conn()
    try:
        if user_id:
            row = conn.execute(
                "SELECT mastery FROM concepts WHERE user_id=? AND title=?",
                (user_id, mission["concept"]),
            ).fetchone()
            if row:
                mastery = row["mastery"]
    finally:
        conn.close()

    return {
        "world": {"id": world["id"], "name": world["name"], "emoji": world["emoji"], "color": world["color"]},
        "mission": {**mission},
        "playbook": playbook,
        "mastery": mastery,
        "level": level_label(mastery),
        "level_index": level_index(mastery),
        "previously_learned": mastery > 0,
    }


class FinishIn(BaseModel):
    user_id: int
    world_id: str
    mission_id: str
    accuracy: float = 1.0          # 0..1 share of quiz answered correctly first try
    time_ms: int = 0
    attempts: int = 1              # total quiz answer taps
    engagement: int = 0           # exploration taps + game tries (a soft signal)
    mode: str = "play"            # play | replay | challenge


@router.post("/mission/finish")
def finish_mission(data: FinishIn):
    world, mission = _find(data.world_id, data.mission_id)
    acc = max(0.0, min(1.0, data.accuracy))
    conn = get_conn()
    try:
        user = conn.execute("SELECT * FROM users WHERE id=?", (data.user_id,)).fetchone()
        if not user:
            raise HTTPException(404, "User not found")

        existing = conn.execute(
            "SELECT id, mastery FROM concepts WHERE user_id=? AND title=?",
            (data.user_id, mission["concept"]),
        ).fetchone()

        playbook = get_playbook(data.world_id, mission)
        method = json.dumps(["story", "game", playbook.get("game", {}).get("type", "play"), "quiz"])
        keywords = make_keywords(mission["concept"], mission["title"], world["subject"], world["name"])

        if existing:
            old = existing["mastery"]
            gain = int(8 + acc * 22)                 # replay nudges mastery up
            new_mastery = min(100, old + gain)
            leveled_up = level_index(new_mastery) > level_index(old)
            conn.execute(
                "UPDATE concepts SET mastery=?, memory_strength=100, last_revised=datetime('now') WHERE id=?",
                (new_mastery, existing["id"]),
            )
        else:
            old = 0
            new_mastery = int(30 + acc * 50)          # first clear: 30..80
            leveled_up = True
            conn.execute(
                """INSERT INTO concepts
                   (user_id, title, subject, world, learned_via, difficulty, mastery, emoji, summary, method, keywords)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (data.user_id, mission["concept"], world["subject"], world["name"],
                 f"{world['name']} Mission", "beginner", new_mastery, mission["emoji"],
                 f"Learned during “{mission['title']}” — story, game & quiz.", method, keywords),
            )

        # XP: base + accuracy bonus (+ first-clear bonus). Challenge mode pays more.
        base = economy.XP["mission"] if not existing else 25
        xp_earned = base + int(acc * 30) + (15 if data.mode == "challenge" else 0)
        coins = economy.COINS["mission"] + (economy.COINS["challenge"] if data.mode == "challenge" else 0)

        # central economy mutation: XP + coins + daily streak + level-up
        result = economy.award(conn, data.user_id, xp=xp_earned, coins=coins,
                               reason=f"mission:{data.world_id}/{data.mission_id}")
        conn.execute(
            "UPDATE users SET last_world=?, last_mission=? WHERE id=?",
            (data.world_id, data.mission_id, data.user_id),
        )
        conn.execute(
            "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
            (data.user_id, "mission",
             f'{{"world":"{data.world_id}","mission":"{data.mission_id}",'
             f'"accuracy":{round(acc,2)},"time_ms":{int(data.time_ms)},'
             f'"attempts":{int(data.attempts)},"mode":"{data.mode}"}}'),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "xp_earned": result["xp_added"],
        "coins_earned": result["coins_added"],
        "streak_bonus": result["streak_bonus"],
        "total_xp": result["total_xp"],
        "total_coins": result["total_coins"],
        "streak": result["streak"],
        "tier_up": result["level_up"],          # named tier level-up (Beginner→Explorer…)
        "concept_saved": mission["concept"],
        "emoji": mission["emoji"],
        "mastery": new_mastery,
        "level": level_label(new_mastery),       # per-concept mastery level
        "leveled_up": leveled_up,                # mastery level changed
        "accuracy": round(acc, 2),
    }
