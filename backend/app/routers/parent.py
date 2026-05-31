"""Parent Dashboard + Premium system (Step 6).

Turns raw learning data into the things parents actually want: skill growth,
interest maps, weak-area detection, an AI Learning DNA report, goals, screen
controls, multi-child management, and a premium subscription.
"""
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..db import get_conn, jload, jdump
from .. import economy

router = APIRouter(prefix="/api/parent", tags=["parent"])

# subject → skill contribution weights (spec 6.3 Section B)
SKILL_WEIGHTS = {
    "Math":       {"logic": 0.5, "problem": 0.5},
    "Science":    {"problem": 0.4, "logic": 0.3, "memory": 0.3},
    "Physics":    {"problem": 0.5, "logic": 0.5},
    "Biology":    {"memory": 0.6, "logic": 0.4},
    "Literature": {"creativity": 0.7, "memory": 0.3},
    "History":    {"memory": 0.6, "creativity": 0.4},
}
SKILL_META = {
    "logic":      {"label": "Logical thinking", "icon": "🧩"},
    "problem":    {"label": "Problem solving", "icon": "🎯"},
    "creativity": {"label": "Creativity",      "icon": "🎨"},
    "memory":     {"label": "Memory retention","icon": "🧠"},
}


def _ensure_parent(conn, child) -> int:
    pid = child["parent_id"]
    if pid:
        return pid
    cur = conn.execute("INSERT INTO parents (pin, plan) VALUES ('1234','free')")
    pid = cur.lastrowid
    conn.execute("UPDATE users SET parent_id=? WHERE id=?", (pid, child["id"]))
    conn.commit()
    return pid


def _skills(concepts, accuracy):
    acc, den = defaultdict(float), defaultdict(float)
    for c in concepts:
        w = SKILL_WEIGHTS.get(c.get("subject"), {"logic": 0.5, "memory": 0.5})
        for skill, wt in w.items():
            acc[skill] += (c.get("mastery", 0)) * wt
            den[skill] += wt
    scores = {}
    for skill in ("logic", "problem", "creativity", "memory"):
        scores[skill] = round(acc[skill] / den[skill]) if den[skill] else 0
    # retention skill blends in overall memory strength + quiz focus
    if concepts:
        retention = round(sum(c.get("memory_strength", 100) for c in concepts) / len(concepts))
        scores["memory"] = round((scores["memory"] + retention) / 2) if scores["memory"] else retention
    scores["focus"] = round(accuracy * 100)
    return scores


def _learning_minutes(events) -> int:
    mins = 0
    for e in events:
        mins += {"mission": 5, "revision": 2, "quick_learn": 1}.get(e["kind"], 0)
    return mins


def _avg_accuracy(conn, child_id) -> float:
    rows = conn.execute(
        "SELECT payload FROM events WHERE user_id=? AND kind='mission'", (child_id,)
    ).fetchall()
    accs = []
    for r in rows:
        try:
            accs.append(jload(r["payload"], {}).get("accuracy", 1))
        except Exception:
            pass
    return round(sum(accs) / len(accs), 2) if accs else 1.0


def _interest_map(concepts):
    by = defaultdict(int)
    for c in concepts:
        by[c.get("subject") or "General"] += 1
    total = sum(by.values()) or 1
    out = [{"label": s, "pct": round(n / total * 100)} for s, n in by.items()]
    out.sort(key=lambda x: x["pct"], reverse=True)
    return out


def _weak_areas(concepts):
    by = defaultdict(list)
    for c in concepts:
        by[c.get("subject") or "General"].append(c)
    weak = []
    for subj, cs in by.items():
        avg = sum(c.get("mastery", 0) for c in cs) / len(cs)
        if avg < 55:
            weak.append({"subject": subj, "avg_mastery": round(avg),
                         "concepts": [c["title"] for c in cs if c.get("mastery", 0) < 55][:3]})
    weak.sort(key=lambda w: w["avg_mastery"])
    return weak


def _load_child(conn, child_id):
    row = conn.execute("SELECT * FROM users WHERE id=?", (child_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Child not found")
    return dict(row)


@router.get("/dashboard/{child_id}")
def dashboard(child_id: int):
    conn = get_conn()
    try:
        child = _load_child(conn, child_id)
        pid = _ensure_parent(conn, child)
        plan = conn.execute("SELECT plan FROM parents WHERE id=?", (pid,)).fetchone()["plan"]
        # refresh memory decay so retention is current
        conn.execute(
            "UPDATE concepts SET memory_strength=MAX(0,100-CAST((julianday('now')-julianday(last_revised))*4 AS INTEGER)) WHERE user_id=?",
            (child_id,))
        conn.commit()
        concepts = [dict(r) for r in conn.execute(
            "SELECT * FROM concepts WHERE user_id=?", (child_id,)).fetchall()]
        events = [dict(r) for r in conn.execute(
            "SELECT kind, created_at, payload FROM events WHERE user_id=?", (child_id,)).fetchall()]
        recent = conn.execute(
            "SELECT COUNT(*) c FROM concepts WHERE user_id=? AND julianday('now')-julianday(learned_at)<=14",
            (child_id,)).fetchone()["c"]
        today_min = _learning_minutes([e for e in events if (e["created_at"] or "")[:10] ==
                                       conn.execute("SELECT date('now') d").fetchone()["d"]])
    finally:
        conn.close()

    accuracy = 1.0
    if events:
        accs = []
        for e in events:
            if e["kind"] == "mission":
                accs.append(jload(e["payload"], {}).get("accuracy", 1))
        accuracy = round(sum(accs) / len(accs), 2) if accs else 1.0

    skills = _skills(concepts, accuracy)
    mastered = sum(1 for c in concepts if c.get("mastery", 0) >= 80)
    retention = round(sum(c.get("memory_strength", 100) for c in concepts) / len(concepts)) if concepts else 100

    skill_list = [{"key": k, **SKILL_META[k], "score": skills.get(k, 0)} for k in SKILL_META]
    top = max(skill_list, key=lambda s: s["score"]) if skill_list else None
    interests = _interest_map(concepts)
    weak = _weak_areas(concepts)
    goal_min = child.get("goal_daily_min") or 20

    # AI-style insights (grounded in real numbers, reassuring tone)
    name = child["name"]
    if not concepts:
        skill_insight = f"{name} is just starting out — early missions will reveal their strengths."
    else:
        skill_insight = (f"{name}'s strongest skill is {top['label'].lower()} ({top['score']}%). "
                         + (f"{recent} new concept(s) learned in the last 2 weeks — great momentum! 🚀"
                            if recent else "A little daily practice will keep skills sharp."))
    interest_insight = (f"{name} gravitates toward {interests[0]['label']} "
                        f"({interests[0]['pct']}% of activity)." if interests else
                        "Interests will emerge as your child explores more worlds.")

    notifications = _parent_notifications(name, concepts, mastered, weak, child.get("streak") or 0)

    return {
        "child": {"id": child["id"], "name": name, "age_group": child["age_group"],
                  "avatar": jload(child.get("avatar"), {}).get("emoji", "🦊"),
                  "tier": economy.tier_for(child["xp"] or 0)["name"], "xp": child["xp"] or 0},
        "plan": plan,
        "summary": {"concepts": len(concepts), "mastered": mastered,
                    "learning_time_today": today_min, "streak": child.get("streak") or 0,
                    "longest_streak": child.get("longest_streak") or 0,
                    "concepts_recent": recent},
        "skills": skill_list, "skill_insight": skill_insight,
        "interests": interests, "interest_insight": interest_insight,
        "weak_areas": weak,
        "retention": {"strength": retention, "label": _ret_label(retention),
                      "due": [c["title"] for c in concepts if c.get("memory_strength", 100) < 60][:5]},
        "goals": {"daily_min": goal_min, "subject": child.get("goal_subject"),
                  "today_min": today_min, "on_track": today_min >= goal_min},
        "controls": {"screen_limit_min": child.get("screen_limit_min") or 60, "used_today": today_min},
        "notifications": notifications,
    }


def _ret_label(s):
    return "Strong" if s >= 70 else "Medium" if s >= 40 else "Weak"


def _parent_notifications(name, concepts, mastered, weak, streak):
    out = []
    if mastered:
        out.append({"icon": "🏆", "text": f"{name} has mastered {mastered} concept(s) — excellent!"})
    if weak:
        out.append({"icon": "⚠️", "text": f"{name} could use a little practice with {weak[0]['subject']}. Revision is ready."})
    if streak >= 3:
        out.append({"icon": "🔥", "text": f"{name} is on a {streak}-day learning streak! 🎉"})
    if not concepts:
        out.append({"icon": "🚀", "text": f"Encourage {name} to start their first mission today."})
    return out


# --- 6.4 AI Learning DNA report (premium) --------------------------------
@router.get("/dna/{child_id}")
def learning_dna(child_id: int):
    conn = get_conn()
    try:
        child = _load_child(conn, child_id)
        pid = _ensure_parent(conn, child)
        plan = conn.execute("SELECT plan FROM parents WHERE id=?", (pid,)).fetchone()["plan"]
        concepts = [dict(r) for r in conn.execute(
            "SELECT * FROM concepts WHERE user_id=?", (child_id,)).fetchall()]
        accuracy = _avg_accuracy(conn, child_id)
    finally:
        conn.close()

    name = child["name"]
    style = (child.get("learning_style") or "games")
    style_name = {"games": "playful, game-based", "stories": "story & narrative",
                  "quizzes": "challenge & quiz"}.get(style, "playful")
    best_method = {"games": "interactive games and visual play",
                   "stories": "storytelling and characters",
                   "quizzes": "quizzes and challenges"}.get(style, "interactive play")

    skills = _skills(concepts, accuracy)
    skill_list = sorted([{"key": k, **SKILL_META[k], "score": skills.get(k, 0)} for k in SKILL_META],
                        key=lambda s: s["score"], reverse=True)
    strengths = [s["label"] for s in skill_list[:2] if s["score"] > 0]
    weaknesses = [s["label"] for s in skill_list if s["score"] < 50][-2:]

    if accuracy >= 0.85:
        attention = "Focused and quick — answers confidently on the first try."
    elif accuracy >= 0.6:
        attention = "Thoughtful — takes time to reason through problems."
    else:
        attention = "Benefits from short, frequent sessions and gentle hints."

    locked = plan == "free"
    report = {
        "name": name, "generated_for": "Monthly Learning DNA",
        "learning_style": style_name,
        "best_method": best_method,
        "strengths": strengths or ["building foundations"],
        "weaknesses": weaknesses or ["no clear weak areas yet"],
        "attention_pattern": attention,
        "skills": skill_list,
        "narrative": (
            f"{name} learns best through {best_method}. "
            f"Their standout strengths are {', '.join(strengths) if strengths else 'still emerging'}. "
            f"{attention} "
            f"To accelerate growth, lean into {best_method} and revisit "
            f"{weaknesses[0] if weaknesses else 'new topics'} with short, fun sessions."
        ),
    }
    return {"locked": locked, "plan": plan,
            "report": (report if not locked else {"name": name, "learning_style": style_name,
                       "teaser": report["narrative"][:120] + "…"})}


# --- 6.10 period reports --------------------------------------------------
@router.get("/report/{child_id}")
def report(child_id: int, period: str = "weekly"):
    days = {"weekly": 7, "monthly": 30, "annual": 365}.get(period, 7)
    conn = get_conn()
    try:
        child = _load_child(conn, child_id)
        learned = conn.execute(
            "SELECT COUNT(*) c FROM concepts WHERE user_id=? AND julianday('now')-julianday(learned_at)<=?",
            (child_id, days)).fetchone()["c"]
        missions = conn.execute(
            "SELECT COUNT(*) c FROM events WHERE user_id=? AND kind='mission' AND julianday('now')-julianday(created_at)<=?",
            (child_id, days)).fetchone()["c"]
        revisions = conn.execute(
            "SELECT COALESCE(SUM(count),0) s FROM revision_logs WHERE user_id=? AND julianday('now')-julianday(created_at)<=?",
            (child_id, days)).fetchone()["s"]
        concepts = [dict(r) for r in conn.execute("SELECT * FROM concepts WHERE user_id=?", (child_id,)).fetchall()]
    finally:
        conn.close()

    interests = _interest_map(concepts)
    weak = _weak_areas(concepts)
    recs = []
    if weak:
        recs.append(f"Revise {weak[0]['subject']} together this {period.replace('ly','')}.")
    if interests:
        recs.append(f"Lean into {interests[0]['label']} — it keeps {child['name']} motivated.")
    recs.append(f"Aim for {child.get('goal_daily_min') or 20} minutes of learning a day.")

    return {
        "period": period, "name": child["name"],
        "learned": learned, "missions": missions, "revisions": revisions,
        "top_interest": interests[0]["label"] if interests else None,
        "recommendations": recs,
        "headline": f"This {period.replace('ly','')}, {child['name']} learned {learned} concept(s) "
                    f"across {missions} mission(s).",
    }


# --- 6.6 goals / 6.7 controls / 6.9 premium ------------------------------
class GoalsIn(BaseModel):
    child_id: int
    daily_min: Optional[int] = None
    subject: Optional[str] = None


@router.post("/goals")
def set_goals(data: GoalsIn):
    conn = get_conn()
    try:
        fields, params = [], []
        if data.daily_min is not None: fields.append("goal_daily_min=?"); params.append(data.daily_min)
        if data.subject is not None: fields.append("goal_subject=?"); params.append(data.subject)
        if fields:
            params.append(data.child_id)
            conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", params)
            conn.commit()
    finally:
        conn.close()
    return {"ok": True}


class ControlsIn(BaseModel):
    child_id: int
    screen_limit_min: int


@router.post("/controls")
def set_controls(data: ControlsIn):
    conn = get_conn()
    try:
        conn.execute("UPDATE users SET screen_limit_min=? WHERE id=?",
                     (data.screen_limit_min, data.child_id))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


class UpgradeIn(BaseModel):
    child_id: int
    plan: str = "premium"   # premium | premium_plus | free


@router.post("/upgrade")
def upgrade(data: UpgradeIn):
    conn = get_conn()
    try:
        child = _load_child(conn, data.child_id)
        pid = _ensure_parent(conn, child)
        conn.execute("UPDATE parents SET plan=? WHERE id=?", (data.plan, pid))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "plan": data.plan}


# --- 6.2 multi-child management ------------------------------------------
@router.get("/children/{child_id}")
def children(child_id: int):
    conn = get_conn()
    try:
        child = _load_child(conn, child_id)
        pid = _ensure_parent(conn, child)
        rows = [dict(r) for r in conn.execute(
            "SELECT id, name, age_group, avatar, xp FROM users WHERE parent_id=? ORDER BY id", (pid,)).fetchall()]
        counts = {r["id"]: conn.execute(
            "SELECT COUNT(*) c FROM concepts WHERE user_id=?", (r["id"],)).fetchone()["c"] for r in rows}
    finally:
        conn.close()
    return {"parent_id": pid, "children": [{
        "id": r["id"], "name": r["name"], "age_group": r["age_group"],
        "avatar": jload(r.get("avatar"), {}).get("emoji", "🦊"),
        "tier": economy.tier_for(r["xp"] or 0)["name"], "concepts": counts[r["id"]],
    } for r in rows]}


class AddChildIn(BaseModel):
    from_child_id: int
    name: str
    age_group: str = "9-12"
    interests: List[str] = []


@router.post("/add-child")
def add_child(data: AddChildIn):
    from ..brain import difficulty_tier
    conn = get_conn()
    try:
        sibling = _load_child(conn, data.from_child_id)
        pid = _ensure_parent(conn, sibling)
        cur = conn.execute(
            """INSERT INTO users (name, age_group, language, tone, voice, avatar, interests,
               learning_style, difficulty_tier, onboarded, streak, parent_id)
               VALUES (?,?,?,?,?,?,?,?,?,1,0,?)""",
            (data.name.strip(), data.age_group, "english", "fun", 1, jdump({"emoji": "🦊"}),
             jdump(data.interests or ["games"]), "games", difficulty_tier(data.age_group), pid),
        )
        new_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "child_id": new_id}
