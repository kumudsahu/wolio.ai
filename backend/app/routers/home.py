"""Homepage engine — one call returns the whole personalized homepage_config.

This is the 'navigation brain + recommendation surface + engagement loop' from
the Step 2 spec. Designed to be a single fast round-trip the client can cache.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn, jload
from .. import economy
from ..brain import (
    WORLDS, rank_worlds, greeting, recommend_action, daily_quest_set,
    quick_learn_for, notifications, time_of_day,
)

router = APIRouter(prefix="/api", tags=["home"])


def _decay_memory(conn, user_id: int) -> None:
    conn.execute(
        """UPDATE concepts
           SET memory_strength = MAX(0,
               100 - CAST((julianday('now') - julianday(last_revised)) * 4 AS INTEGER))
           WHERE user_id=?""",
        (user_id,),
    )


def _ensure_today_quests(conn, user_id: int, tier: int, day: str) -> None:
    """Materialize today's quest set once per day (idempotent)."""
    existing = conn.execute(
        "SELECT COUNT(*) c FROM daily_quests WHERE user_id=? AND day=?", (user_id, day)
    ).fetchone()["c"]
    if existing:
        return
    for q in daily_quest_set(tier):
        conn.execute(
            """INSERT OR IGNORE INTO daily_quests
               (user_id, day, task_id, icon, label, target, reward)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id, day, q["task_id"], q["icon"], q["label"], q["target"], q["reward"]),
        )


def _quest_progress(conn, user_id: int, day: str) -> dict:
    """Live progress from today's events — single source of truth."""
    def count(kind):
        return conn.execute(
            "SELECT COUNT(*) c FROM events WHERE user_id=? AND kind=? AND date(created_at)=?",
            (user_id, kind, day),
        ).fetchone()["c"]
    revised = conn.execute(
        "SELECT COALESCE(SUM(CAST(json_extract(payload,'$.count') AS INTEGER)),0) s "
        "FROM events WHERE user_id=? AND kind='revision' AND date(created_at)=?",
        (user_id, day),
    ).fetchone()["s"]
    return {"learn": count("mission"), "quick": count("quick_learn"), "revise": revised or 0}


def _hour_now() -> int:
    return datetime.now(timezone.utc).astimezone().hour


@router.get("/homepage/{user_id}")
def homepage(user_id: int):
    conn = get_conn()
    try:
        urow = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not urow:
            raise HTTPException(404, "User not found")
        user = dict(urow)
        interests = jload(user.get("interests"), [])

        _decay_memory(conn, user_id)
        concepts = [dict(r) for r in conn.execute(
            "SELECT * FROM concepts WHERE user_id=? ORDER BY learned_at DESC", (user_id,)
        ).fetchall()]

        day = conn.execute("SELECT date('now') d").fetchone()["d"]
        _ensure_today_quests(conn, user_id, user.get("difficulty_tier") or 1, day)
        progress = _quest_progress(conn, user_id, day)

        # Award XP + coins for any quest that just crossed its target (once).
        quest_rows = [dict(r) for r in conn.execute(
            "SELECT * FROM daily_quests WHERE user_id=? AND day=? ORDER BY id", (user_id, day)
        ).fetchall()]
        xp = user.get("xp") or 0
        coins = user.get("coins") or 0
        for q in quest_rows:
            done = progress.get(q["task_id"], 0) >= q["target"]
            if done and not q["claimed"]:
                res = economy.award(conn, user_id, xp=q["reward"], coins=economy.COINS["quest"],
                                    reason=f"quest:{q['task_id']}")
                xp, coins = res["total_xp"], res["total_coins"]
                conn.execute("UPDATE daily_quests SET claimed=1 WHERE id=?", (q["id"],))

        # Achievements: detect & record newly-earned badges.
        missions_done = conn.execute(
            "SELECT COUNT(*) c FROM events WHERE user_id=? AND kind='mission'", (user_id,)).fetchone()["c"]
        revisions = conn.execute(
            "SELECT COALESCE(SUM(count),0) s FROM revision_logs WHERE user_id=?", (user_id,)).fetchone()["s"]
        mastered = sum(1 for c in concepts if c["mastery"] >= 80)
        ach_stats = {
            "concepts": len(concepts), "mastered": mastered,
            "longest_streak": user.get("longest_streak") or 0,
            "missions": missions_done, "coins_earned": economy.coins_earned_total(conn, user_id),
            "tier_index": economy.tier_index(xp), "revisions": revisions,
        }
        ach = economy.sync_achievements(conn, user_id, ach_stats)
        # award coins for each freshly-earned achievement
        for _ in ach["newly"]:
            res = economy.award(conn, user_id, coins=economy.COINS["achievement"], reason="achievement")
            coins = res["total_coins"]
        conn.commit()
        streak = conn.execute("SELECT streak FROM users WHERE id=?", (user_id,)).fetchone()["streak"]
    finally:
        conn.close()

    level = economy.level_block(xp)

    hour = _hour_now()
    slot = time_of_day(hour)
    completed_titles = {c["title"] for c in concepts}
    needs_revision = [c for c in concepts if c["memory_strength"] < 60]
    ranked = rank_worlds(interests)

    hero = recommend_action(
        name=user["name"], ranked_worlds=ranked,
        last_world=user.get("last_world"), last_mission=user.get("last_mission"),
        completed_titles=completed_titles, needs_revision=needs_revision,
        hour=hour, concepts_count=len(concepts),
    )

    # Continue card — resume exact last (or recommended) world.
    cont = None
    cw = next((w for w in ranked if w["id"] == user.get("last_world")), None) or (ranked[0] if ranked else None)
    if cw:
        total = len(cw["missions"])
        done = sum(1 for m in cw["missions"] if m["concept"] in completed_titles)
        nxt = next((m for m in cw["missions"] if m["concept"] not in completed_titles), cw["missions"][-1])
        cont = {
            "world_id": cw["id"], "world_name": cw["name"], "color": cw["color"], "world_emoji": cw["emoji"],
            "mission_id": nxt["id"], "mission_title": nxt["title"], "mission_emoji": nxt["emoji"],
            "progress": round(done / max(1, total) * 100),
        }

    # Worlds with progress / level / unlock / recommended flag.
    worlds_out = []
    for i, w in enumerate(ranked):
        total = len(w["missions"])
        done = sum(1 for m in w["missions"] if m["concept"] in completed_titles)
        worlds_out.append({
            "id": w["id"], "name": w["name"], "emoji": w["emoji"], "color": w["color"],
            "subject": w["subject"], "tagline": w["tagline"],
            "total": total, "done": done,
            "progress": round(done / max(1, total) * 100),
            "level": done + 1,
            "unlocked": i < 2 or xp >= i * 60,   # first two free; rest unlock with XP
            "recommended": w["id"] == hero.get("world_id"),
        })

    avg_strength = round(sum(c["memory_strength"] for c in concepts) / len(concepts)) if concepts else 100
    mastered = sum(1 for c in concepts if c["mastery"] >= 80)
    recent = None
    if concepts:
        c = concepts[0]
        recent = {"title": c["title"], "emoji": c["emoji"], "learned_at": c["learned_at"]}

    quests_out = [{
        "id": q["task_id"], "icon": q["icon"], "label": q["label"],
        "target": q["target"], "reward": q["reward"],
        "progress": min(progress.get(q["task_id"], 0), q["target"]),
        "done": progress.get(q["task_id"], 0) >= q["target"],
    } for q in quest_rows]

    return {
        "greeting": greeting(user["name"], hour),
        "hero": hero,
        "continue": cont,
        "worlds": worlds_out,
        "quick_learn": quick_learn_for(interests),
        "daily_quests": quests_out,
        "quests_done": sum(1 for q in quests_out if q["done"]),
        "memory": {"recent": recent, "strength": avg_strength, "due_count": len(needs_revision)},
        "coins": coins,
        "level": level,                       # tier, next_tier, progress, nudge
        "new_achievements": ach["newly"],     # ids freshly unlocked this load
        "stats": {
            "xp": xp, "coins": coins, "streak": streak,
            "concepts": len(concepts), "mastered": mastered,
            "tier": level["tier"], "tier_index": level["tier_index"],
        },
        "notifications": notifications(streak, needs_revision, len(concepts), slot),
        "user": {"name": user["name"], "avatar": jload(user.get("avatar"), {}), "tone": user.get("tone")},
    }


class QuickLearnIn(BaseModel):
    user_id: int
    id: str
    title: str
    subject: str = "Science"
    emoji: str = "⚡"
    save: bool = True


@router.post("/quick-learn")
def quick_learn_seen(data: QuickLearnIn):
    """Log a Quick Learn view (counts toward the daily quest); optionally save to memory."""
    conn = get_conn()
    try:
        if not conn.execute("SELECT 1 FROM users WHERE id=?", (data.user_id,)).fetchone():
            raise HTTPException(404, "User not found")
        conn.execute(
            "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
            (data.user_id, "quick_learn", f'{{"id":"{data.id}"}}'),
        )
        saved = False
        if data.save:
            exists = conn.execute(
                "SELECT 1 FROM concepts WHERE user_id=? AND title=?", (data.user_id, data.title)
            ).fetchone()
            if not exists:
                from ..content import make_keywords
                conn.execute(
                    """INSERT INTO concepts
                       (user_id, title, subject, world, learned_via, difficulty, mastery, emoji, summary, method, keywords)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (data.user_id, data.title, data.subject, "Quick Learn", "Quick Learn",
                     "beginner", 20, data.emoji, "Picked up from a Quick Learn bite.",
                     '["quick_learn"]', make_keywords(data.title, data.subject)),
                )
                saved = True
        # small coin reward for engaging with a bite
        economy.award(conn, data.user_id, coins=economy.COINS["quick_learn"], reason="quick_learn")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "saved": saved}
