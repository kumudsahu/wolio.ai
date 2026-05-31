"""AI Mentor — the guided, walled-garden child-safe chat endpoint.

Pipeline (Child-Safe AI Architecture):
    input → INPUT FILTER → AI → OUTPUT FILTER → response
Plus emotional-safety handling, parent topic restrictions, age adaptation,
and logging (ai_chat topics + safety_block categories) for the parent panel.
"""
import json
import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from ..db import get_conn, jload
from ..brain import mentor_reply
from .. import safety

router = APIRouter(prefix="/api", tags=["mentor"])


class MentorIn(BaseModel):
    user_id: Optional[int] = None
    message: str
    mode: str = "fun"  # fun | quick | quiz
    history: Optional[List[dict]] = None       # last few turns for session memory
    current_topic: Optional[str] = None        # what they're learning right now
    # allow anonymous chat (e.g. during onboarding) with inline context
    name: Optional[str] = None
    interests: Optional[List[str]] = None
    language: Optional[str] = None
    tone: Optional[str] = None
    age_group: Optional[str] = None


def _log(user_id, kind, payload: dict):
    if not user_id:
        return
    conn = get_conn()
    try:
        conn.execute("INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
                     (user_id, kind, json.dumps(payload)))
        conn.commit()
    finally:
        conn.close()


def _topic_of(message: str) -> str:
    """Best-effort short topic label for parent chat summaries."""
    t = re.sub(r"(?i)\b(explain|what is|what's|tell me about|how does|why do|why does|quiz me on)\b", "", message)
    t = re.sub(r"[^\w\s]", "", t).strip()
    return (t[:40] or "general").lower()


@router.post("/mentor")
def chat(data: MentorIn):
    restricted, ctx_extra = [], {}
    if data.user_id:
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE id=?", (data.user_id,)).fetchone()
            if row:
                rd = dict(row)
                ctx_extra = {
                    "name": rd["name"], "interests": jload(rd.get("interests"), []),
                    "language": rd.get("language"), "tone": rd.get("tone"),
                    "age_group": rd.get("age_group"),
                }
                # parent-configured topic restrictions (goal_subject is reused as a soft block list elsewhere;
                # explicit restricted topics live in a JSON column if present)
                restricted = jload(rd.get("restricted_topics"), []) if "restricted_topics" in rd.keys() else []
        finally:
            conn.close()

    # LAYER 1 — input filter (block / emotional / sensitive / restricted / allow)
    gate = safety.classify_input(data.message, restricted_topics=restricted)
    if gate["action"] in ("block", "restricted"):
        _log(data.user_id, "safety_block", {"category": gate["category"], "topic": _topic_of(data.message)})
        return {"reply": gate["redirect"], "source": "safety", "mode": data.mode,
                "blocked": True, "category": gate["category"]}
    if gate["action"] == "emotional":
        _log(data.user_id, "safety_emotional", {"category": gate["category"]})
        return {"reply": gate["redirect"], "source": "safety", "mode": data.mode,
                "blocked": False, "emotional": True}

    ctx = {"name": data.name or "buddy", "interests": data.interests or [],
           "language": data.language or "hinglish", "tone": data.tone or "fun",
           "age_group": data.age_group or "9-12"}
    ctx.update({k: v for k, v in ctx_extra.items() if v})
    if data.current_topic:
        ctx["recent_learning"] = data.current_topic

    sensitive = gate["action"] == "sensitive"
    result = mentor_reply(data.message, ctx, mode=data.mode, history=data.history, sensitive=sensitive)

    # LAYER 2 — output filter (scrub links/PII, block unsafe + manipulation/dependency)
    safe_reply = safety.sanitize_output(result["reply"])

    # log a kid-safe chat summary for the parent panel (topic only, never raw text)
    _log(data.user_id, "ai_chat", {"topic": _topic_of(data.message), "mode": data.mode,
                                    "sensitive": sensitive})
    return {"reply": safe_reply, "source": result["source"], "mode": data.mode, "blocked": False}
