"""Life Learning Timeline (LLT) + Memory engine — the signature feature.

'Every concept a student ever learns is saved, organized, and instantly
revisable.'  This module is the Step-4 Memory & Learning Timeline System:
structured concept memories, a year→month timeline, memory cards, search,
revision modes, memory-strength, badges, and a parent growth view.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from collections import defaultdict, OrderedDict

from ..db import get_conn, jload
from .. import economy

router = APIRouter(prefix="/api", tags=["timeline"])

_MONTHS = ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]


def _decay_memory(conn, user_id: int) -> None:
    """Memory strength decays with time since last revision (spaced-repetition feel)."""
    conn.execute(
        """UPDATE concepts
           SET memory_strength = MAX(0,
               100 - CAST((julianday('now') - julianday(last_revised)) * 4 AS INTEGER))
           WHERE user_id=?""",
        (user_id,),
    )


def retention_label(strength: int) -> str:
    if strength >= 70:
        return "Strong"
    if strength >= 40:
        return "Medium"
    return "Weak"


def memory_suggestions(concepts: list, top: int = 2) -> list:
    """Homepage 'Your Memory' shortcut — top-N concepts to resurface.

    urgency_score rises with time since last seen and falling mastery/strength.
    Each card gets a state: fresh | mid | weak (spec section 7).
    """
    out = []
    for c in concepts:
        days = c.get("_days_since") or 0
        strength = c.get("memory_strength", 100)
        mastery = c.get("mastery", 0)
        urgency = (100 - strength) + days * 3 + (20 if mastery < 70 else 0)
        if days < 1:
            state, urgency = "fresh", urgency * 0.2          # just learned — low urgency
        elif strength < 60 or days > 7:
            state = "weak"
        else:
            state = "mid"
        out.append({
            "concept_id": c["id"], "topic": c["title"], "emoji": c.get("emoji") or "✨",
            "days": days, "state": state, "mastery": mastery,
            "memory_strength": strength, "urgency": round(urgency, 1),
        })
    out.sort(key=lambda x: x["urgency"], reverse=True)
    return out[:top]


@router.get("/memory-suggestions/{user_id}")
def get_memory_suggestions(user_id: int):
    conn = get_conn()
    try:
        _decay_memory(conn, user_id)
        conn.commit()
        rows = conn.execute(
            "SELECT *, CAST(julianday('now')-julianday(last_revised) AS INTEGER) _days_since "
            "FROM concepts WHERE user_id=? ORDER BY last_revised ASC", (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return {"suggestions": memory_suggestions([dict(r) for r in rows])}


def _card(c: dict) -> dict:
    """Shape a concept row into a Memory Card."""
    return {
        "id": c["id"], "title": c["title"], "emoji": c.get("emoji") or "✨",
        "subject": c.get("subject"), "world": c.get("world"),
        "learned_via": c.get("learned_via"), "summary": c.get("summary"),
        "mastery": c.get("mastery", 0), "memory_strength": c.get("memory_strength", 100),
        "retention": retention_label(c.get("memory_strength", 100)),
        "learned_at": c.get("learned_at"), "last_revised": c.get("last_revised"),
        "revision_count": c.get("revision_count", 0),
        "method": jload(c.get("method"), []),
    }


def _badges(total, mastered, strength, revisions):
    defs = [
        {"id": "first", "icon": "🌱", "label": "First Memory", "earned": total >= 1, "hint": "Learn 1 concept"},
        {"id": "curious", "icon": "🔭", "label": "Curious Mind", "earned": total >= 5, "hint": "Learn 5 concepts"},
        {"id": "master", "icon": "🧠", "label": "Memory Master", "earned": mastered >= 3, "hint": "Master 3 concepts"},
        {"id": "revisionist", "icon": "🔁", "label": "Revisionist", "earned": revisions >= 10, "hint": "Revise 10 times"},
        {"id": "strong", "icon": "💪", "label": "Strong Brain", "earned": strength >= 80, "hint": "Keep memory ≥80%"},
        {"id": "centurion", "icon": "💯", "label": "Centurion", "earned": total >= 100, "hint": "Learn 100 concepts"},
    ]
    return defs


def _subjects(concepts: list) -> list:
    by = defaultdict(list)
    for c in concepts:
        by[c.get("subject") or "General"].append(c)
    out = []
    for subj, cs in by.items():
        avg = round(sum(x.get("mastery", 0) for x in cs) / len(cs))
        out.append({"subject": subj, "count": len(cs), "avg_mastery": avg,
                    "level": "Strong" if avg >= 60 else "Growing" if avg >= 35 else "Needs work"})
    out.sort(key=lambda s: s["avg_mastery"], reverse=True)
    return out


@router.get("/timeline/{user_id}")
def get_timeline(user_id: int):
    conn = get_conn()
    try:
        _decay_memory(conn, user_id)
        conn.commit()
        rows = conn.execute(
            "SELECT * FROM concepts WHERE user_id=? ORDER BY learned_at DESC", (user_id,)
        ).fetchall()
        revisions = conn.execute(
            "SELECT COALESCE(SUM(count),0) s FROM revision_logs WHERE user_id=?", (user_id,)
        ).fetchone()["s"]
    finally:
        conn.close()

    concepts = [dict(r) for r in rows]
    cards = [_card(c) for c in concepts]

    # group by year → month
    by_year = OrderedDict()
    for c in cards:
        ts = c.get("learned_at") or "2026-01"
        year, mon = ts[:4], int((ts[5:7] or "1"))
        by_year.setdefault(year, OrderedDict())
        by_year[year].setdefault(mon, []).append(c)

    years = []
    for year, months in by_year.items():
        all_c = [c for ms in months.values() for c in ms]
        years.append({
            "year": year, "count": len(all_c), "concepts": all_c,
            "months": [{"key": f"{year}-{m:02d}", "label": _MONTHS[m], "concepts": cs}
                       for m, cs in sorted(months.items(), reverse=True)],
        })
    years.sort(key=lambda y: y["year"], reverse=True)

    total = len(concepts)
    avg_strength = round(sum(c["memory_strength"] for c in concepts) / total) if total else 100
    mastered = sum(1 for c in concepts if c["mastery"] >= 80)
    needs_revision = [c for c in cards if c["memory_strength"] < 60]

    return {
        "total_concepts": total,
        "memory_strength": avg_strength,
        "retention_label": retention_label(avg_strength),
        "mastered": mastered,
        "revisions": revisions,
        "years": years,
        "needs_revision": needs_revision[:5],
        "subjects": _subjects(concepts),
        "badges": _badges(total, mastered, avg_strength, revisions),
    }


@router.get("/concept/{user_id}/{concept_id}")
def memory_card(user_id: int, concept_id: int):
    """Open one Memory Card with AI smart-recall + a suggested next action."""
    conn = get_conn()
    try:
        _decay_memory(conn, user_id)
        conn.commit()
        row = conn.execute(
            "SELECT * FROM concepts WHERE id=? AND user_id=?", (concept_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Concept not found")
        c = dict(row)
        related = conn.execute(
            "SELECT title, emoji, id FROM concepts WHERE user_id=? AND subject=? AND id!=? LIMIT 4",
            (user_id, c.get("subject"), concept_id),
        ).fetchall()
        # how long ago (smart recall)
        days = conn.execute(
            "SELECT CAST(julianday('now') - julianday(?) AS INTEGER) d", (c["learned_at"],)
        ).fetchone()["d"] or 0
    finally:
        conn.close()

    card = _card(c)
    recall = _recall_phrase(days)
    strength = card["memory_strength"]
    if strength < 40:
        action = {"kind": "revise", "text": "This is fading fast — let's revise it now! 🧠"}
    elif strength < 70:
        action = {"kind": "revise", "text": "A quick revision will lock this back in 💪"}
    else:
        action = {"kind": "challenge", "text": "You're strong here — ready for a challenge? 🔥"}

    return {
        "card": card, "smart_recall": recall, "days_ago": days, "action": action,
        "related": [{"id": r["id"], "title": r["title"], "emoji": r["emoji"]} for r in related],
    }


def _recall_phrase(days: int) -> str:
    if days <= 0:
        return "You learned this today 🌟"
    if days == 1:
        return "You learned this yesterday"
    if days < 7:
        return f"You learned this {days} days ago"
    if days < 60:
        return f"You learned this {days // 7} week(s) ago"
    return f"You learned this {days // 30} month(s) ago"


@router.get("/timeline/{user_id}/search")
def search_brain(user_id: int, q: str = ""):
    """'Search Your Brain' — Google inside your own brain (title/subject/summary/keywords)."""
    q = q.strip()
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT * FROM concepts
               WHERE user_id=? AND (title LIKE ? OR subject LIKE ? OR summary LIKE ? OR keywords LIKE ?)
               ORDER BY learned_at DESC""",
            (user_id, f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    finally:
        conn.close()
    return {"query": q, "results": [_card(dict(r)) for r in rows]}


# scope/mode → SQL filter for the revision deck
_SCOPE_SQL = {
    "quick": " AND julianday('now') - julianday(learned_at) <= 7",   # recent
    "last_7": " AND julianday('now') - julianday(learned_at) <= 7",
    "smart": " AND memory_strength < 60",                            # weak areas
    "needs_revision": " AND memory_strength < 60",
    "last_year": " AND julianday('now') - julianday(learned_at) <= 365",
    "full": "", "all": "", "challenge": "",
}


class ReviseIn(BaseModel):
    user_id: int
    scope: str = "smart"   # quick | smart | full | challenge (legacy scopes still work)


@router.post("/timeline/revise")
def revise(data: ReviseIn):
    """Instant revision — returns a flash-card deck, refreshes memory, logs the session."""
    where = "user_id=?" + _SCOPE_SQL.get(data.scope, "")
    order = "memory_strength DESC" if data.scope == "challenge" else "memory_strength ASC"
    conn = get_conn()
    try:
        rows = conn.execute(
            f"SELECT * FROM concepts WHERE {where} ORDER BY {order}", (data.user_id,)
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            conn.executemany(
                "UPDATE concepts SET memory_strength=100, last_revised=datetime('now'),"
                " revision_count=COALESCE(revision_count,0)+1 WHERE id=?",
                [(i,) for i in ids],
            )
            conn.execute(
                "INSERT INTO revision_logs (user_id, mode, count) VALUES (?,?,?)",
                (data.user_id, data.scope, len(ids)),
            )
            # keep the daily-quest 'revise' counter in sync
            conn.execute(
                "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
                (data.user_id, "revision", f'{{"count":{len(ids)}}}'),
            )
            # reward the revision (XP + coins, advances streak)
            reward = economy.award(conn, data.user_id, xp=economy.XP["revision"],
                                   coins=economy.COINS["revision"], reason=f"revision:{data.scope}")
            conn.commit()
    finally:
        conn.close()

    cards = [{
        "id": r["id"], "title": r["title"], "emoji": r["emoji"], "subject": r["subject"],
        "learned_via": r["learned_via"], "summary": r["summary"],
        "front": f"What did you learn about {r['title']}?",
    } for r in rows]
    out = {"scope": data.scope, "count": len(cards), "cards": cards}
    if ids:
        out["reward"] = {"xp": reward["xp_added"], "coins": reward["coins_added"], "tier_up": reward["level_up"]}
    return out


class ConceptReviseIn(BaseModel):
    user_id: int
    concept_id: int


@router.post("/concept/revise")
def revise_concept(data: ConceptReviseIn):
    """Revise a single concept from its Memory Card (refresh + log)."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM concepts WHERE id=? AND user_id=?", (data.concept_id, data.user_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Concept not found")
        conn.execute(
            "UPDATE concepts SET memory_strength=100, last_revised=datetime('now'),"
            " revision_count=COALESCE(revision_count,0)+1 WHERE id=?",
            (data.concept_id,),
        )
        conn.execute(
            "INSERT INTO revision_logs (user_id, concept_id, mode, count) VALUES (?,?,?,?)",
            (data.user_id, data.concept_id, "card", 1),
        )
        conn.execute(
            "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
            (data.user_id, "revision", '{"count":1}'),
        )
        economy.award(conn, data.user_id, xp=economy.XP["revision"],
                     coins=economy.COINS["revision"], reason="revision:card")
        conn.commit()
        r = dict(row)
    finally:
        conn.close()
    return {"card": {
        "id": r["id"], "title": r["title"], "emoji": r["emoji"], "subject": r["subject"],
        "learned_via": r["learned_via"], "summary": r["summary"],
        "front": f"What did you learn about {r['title']}?",
    }}


@router.get("/insights/{user_id}")
def insights(user_id: int):
    """Parent growth view + long-term intelligence snapshot."""
    conn = get_conn()
    try:
        _decay_memory(conn, user_id)
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        rows = conn.execute("SELECT * FROM concepts WHERE user_id=?", (user_id,)).fetchall()
        # concepts learned per month (growth graph)
        growth = conn.execute(
            """SELECT strftime('%Y-%m', learned_at) ym, COUNT(*) c
               FROM concepts WHERE user_id=? GROUP BY ym ORDER BY ym""",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    concepts = [dict(r) for r in rows]
    subjects = _subjects(concepts)
    strong = [s["subject"] for s in subjects if s["avg_mastery"] >= 60]
    weak = [s["subject"] for s in subjects if s["avg_mastery"] < 35]
    total = len(concepts)
    mastered = sum(1 for c in concepts if c["mastery"] >= 80)
    avg_strength = round(sum(c["memory_strength"] for c in concepts) / total) if total else 100
    interests = jload(user["interests"], [])

    growth_series = [{"label": _MONTHS[int(g["ym"][5:7])][:3], "ym": g["ym"], "count": g["c"]} for g in growth]

    name = user["name"]
    if total == 0:
        intelligence = f"{name} is just getting started — the journey begins now! 🚀"
    else:
        top = subjects[0]["subject"] if subjects else "learning"
        intelligence = (f"{name} has learned {total} concept{'s' if total != 1 else ''} and shows real "
                        f"strength in {top}. " +
                        (f"Loves {', '.join(interests[:2])}. " if interests else "") +
                        ("Keep the daily streak alive for compounding growth 🔥"))

    return {
        "name": name,
        "total_concepts": total,
        "mastered": mastered,
        "memory_strength": avg_strength,
        "retention_label": retention_label(avg_strength),
        "total_xp": user["xp"], "streak": user["streak"],
        "subjects": subjects,
        "strong": strong, "weak": weak,
        "growth": growth_series,
        "top_interests": interests,
        "intelligence": intelligence,
    }
