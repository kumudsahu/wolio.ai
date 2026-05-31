"""Life Learning Timeline (LLT) — the signature feature.

'Every concept a student ever learns is saved, organized, and instantly revisable.'
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from collections import defaultdict

from ..db import get_conn

router = APIRouter(prefix="/api", tags=["timeline"])


def _decay_memory(conn, user_id: int) -> None:
    """Memory strength decays with time since last revision (spaced-repetition feel)."""
    conn.execute(
        """UPDATE concepts
           SET memory_strength = MAX(0,
               100 - CAST((julianday('now') - julianday(last_revised)) * 4 AS INTEGER))
           WHERE user_id=?""",
        (user_id,),
    )


@router.get("/timeline/{user_id}")
def get_timeline(user_id: int):
    conn = get_conn()
    try:
        _decay_memory(conn, user_id)
        conn.commit()
        rows = conn.execute(
            "SELECT * FROM concepts WHERE user_id=? ORDER BY learned_at DESC", (user_id,)
        ).fetchall()
    finally:
        conn.close()

    concepts = [dict(r) for r in rows]
    by_year = defaultdict(list)
    for c in concepts:
        year = (c.get("learned_at") or "")[:4] or "2026"
        by_year[year].append(c)

    years = [{"year": y, "concepts": cs, "count": len(cs)}
             for y, cs in sorted(by_year.items(), reverse=True)]

    total = len(concepts)
    avg_strength = round(sum(c["memory_strength"] for c in concepts) / total) if total else 0
    mastered = sum(1 for c in concepts if c["mastery"] >= 80)
    needs_revision = [c for c in concepts if c["memory_strength"] < 60]

    return {
        "total_concepts": total,
        "memory_strength": avg_strength,
        "mastered": mastered,
        "years": years,
        "needs_revision": needs_revision[:5],
    }


@router.get("/timeline/{user_id}/search")
def search_brain(user_id: int, q: str = ""):
    """'Search Your Brain' — Google inside your own brain."""
    q = q.strip()
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT * FROM concepts
               WHERE user_id=? AND (title LIKE ? OR subject LIKE ? OR summary LIKE ?)
               ORDER BY learned_at DESC""",
            (user_id, f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    finally:
        conn.close()
    return {"query": q, "results": [dict(r) for r in rows]}


class ReviseIn(BaseModel):
    user_id: int
    scope: str = "needs_revision"  # last_7 | last_year | all | needs_revision


@router.post("/timeline/revise")
def revise(data: ReviseIn):
    """1-Click Full Revision — returns a flash-card deck for the chosen scope."""
    where = "user_id=?"
    params = [data.user_id]
    if data.scope == "last_7":
        where += " AND julianday('now') - julianday(learned_at) <= 7"
    elif data.scope == "last_year":
        where += " AND julianday('now') - julianday(learned_at) <= 365"
    elif data.scope == "needs_revision":
        where += " AND memory_strength < 60"

    conn = get_conn()
    try:
        rows = conn.execute(
            f"SELECT * FROM concepts WHERE {where} ORDER BY memory_strength ASC", params
        ).fetchall()
        # Revising refreshes memory strength.
        ids = [r["id"] for r in rows]
        if ids:
            conn.executemany(
                "UPDATE concepts SET memory_strength=100, last_revised=datetime('now') WHERE id=?",
                [(i,) for i in ids],
            )
            conn.commit()
    finally:
        conn.close()

    cards = [{
        "title": r["title"], "emoji": r["emoji"], "subject": r["subject"],
        "learned_via": r["learned_via"], "summary": r["summary"],
        "front": f"What did you learn about {r['title']}?",
    } for r in rows]
    return {"scope": data.scope, "count": len(cards), "cards": cards}
