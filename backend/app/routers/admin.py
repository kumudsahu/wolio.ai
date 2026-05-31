"""Internal admin tools (Step 7.11 analytics + 7.5 content ops).

Guarded by a simple ADMIN_KEY (env, default 'wolio-admin'). In production this
sits behind staff SSO — documented in ARCHITECTURE.md. Powers the /admin page.
"""
import os
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from ..db import get_conn
from ..brain import WORLDS
from ..content import PLAYBOOKS, get_playbook
from .. import economy

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_KEY = os.getenv("ADMIN_KEY", "wolio-admin")


def _auth(key: Optional[str]):
    if key != ADMIN_KEY:
        raise HTTPException(401, "Admin key required")


@router.get("/analytics")
def analytics(key: Optional[str] = None, x_admin_key: Optional[str] = Header(None)):
    _auth(key or x_admin_key)
    conn = get_conn()
    try:
        users = conn.execute("SELECT COUNT(*) c FROM users WHERE onboarded=1").fetchone()["c"]
        # DAU / WAU from activity events
        dau = conn.execute(
            "SELECT COUNT(DISTINCT user_id) c FROM events WHERE date(created_at)=date('now')").fetchone()["c"]
        wau = conn.execute(
            "SELECT COUNT(DISTINCT user_id) c FROM events WHERE julianday('now')-julianday(created_at)<=7").fetchone()["c"]
        # retention: of users who joined >1 day ago, how many were active in last 2 days
        cohort = conn.execute(
            "SELECT COUNT(*) c FROM users WHERE julianday('now')-julianday(created_at)>=1 AND onboarded=1").fetchone()["c"]
        retained = conn.execute(
            """SELECT COUNT(DISTINCT u.id) c FROM users u JOIN events e ON e.user_id=u.id
               WHERE julianday('now')-julianday(u.created_at)>=1
               AND julianday('now')-julianday(e.created_at)<=2""").fetchone()["c"]
        sessions = conn.execute("SELECT COUNT(*) c FROM events WHERE kind='mission'").fetchone()["c"]
        # funnel / drop-offs across the mission flow (proxy: started vs completed)
        missions_done = conn.execute("SELECT COUNT(*) c FROM events WHERE kind='mission'").fetchone()["c"]
        concepts = conn.execute("SELECT COUNT(*) c FROM concepts").fetchone()["c"]
        revisions = conn.execute("SELECT COALESCE(SUM(count),0) s FROM revision_logs").fetchone()["s"]
        quick = conn.execute("SELECT COUNT(*) c FROM events WHERE kind='quick_learn'").fetchone()["c"]
        safety_blocks = conn.execute("SELECT COUNT(*) c FROM events WHERE kind='safety_block'").fetchone()["c"]
        premium = conn.execute("SELECT COUNT(*) c FROM parents WHERE plan!='free'").fetchone()["c"]
        parents = conn.execute("SELECT COUNT(*) c FROM parents").fetchone()["c"]
        # event mix
        mix = [{"kind": r["kind"], "count": r["c"]} for r in conn.execute(
            "SELECT kind, COUNT(*) c FROM events GROUP BY kind ORDER BY c DESC").fetchall()]
        xp_total = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE kind='xp'").fetchone()["s"]
        coins_total = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE kind='coin' AND amount>0").fetchone()["s"]
    finally:
        conn.close()

    return {
        "users": users, "dau": dau, "wau": wau,
        "retention_pct": round(retained / cohort * 100) if cohort else 0,
        "sessions": sessions,
        "engagement": {"missions": missions_done, "concepts": concepts,
                       "revisions": revisions, "quick_learn": quick},
        "safety_blocks": safety_blocks,
        "monetization": {"parents": parents, "premium": premium,
                         "conversion_pct": round(premium / parents * 100) if parents else 0},
        "economy": {"xp_awarded": xp_total, "coins_awarded": coins_total},
        "event_mix": mix,
    }


@router.get("/content")
def content(key: Optional[str] = None, x_admin_key: Optional[str] = Header(None)):
    """Content catalog + health (7.5). Surfaces authored vs auto-generated missions."""
    _auth(key or x_admin_key)
    worlds, missions_total, authored = [], 0, 0
    for w in WORLDS:
        ms = []
        for m in w["missions"]:
            missions_total += 1
            key_ = f"{w['id']}/{m['id']}"
            is_authored = key_ in PLAYBOOKS
            authored += 1 if is_authored else 0
            pb = get_playbook(w["id"], m)
            ms.append({
                "id": m["id"], "title": m["title"], "concept": m["concept"],
                "chapter": m.get("chapter"), "authored": is_authored,
                "story_lines": len(pb.get("story", [])),
                "game_type": pb.get("game", {}).get("type"),
                "quiz_count": len(pb.get("quiz", [])),
            })
        worlds.append({"id": w["id"], "name": w["name"], "emoji": w["emoji"],
                       "subject": w["subject"], "missions": ms})
    return {
        "worlds": len(WORLDS), "missions": missions_total,
        "authored": authored, "auto_generated": missions_total - authored,
        "coverage_pct": round(authored / missions_total * 100) if missions_total else 0,
        "shop_items": len(economy.SHOP), "achievements": len(economy.ACHIEVEMENTS),
        "catalog": worlds,
    }
