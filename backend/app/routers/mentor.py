from fastapi import APIRouter, HTTPException
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


def _log_safety(user_id, reason, message):
    if not user_id:
        return
    conn = get_conn()
    try:
        conn.execute("INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
                     (user_id, "safety_block", f'{{"reason":"{reason}"}}'))
        conn.commit()
    finally:
        conn.close()


@router.post("/mentor")
def chat(data: MentorIn):
    # 7.10 safety: screen the child's message before doing anything else.
    gate = safety.check_input(data.message)
    if not gate["safe"]:
        _log_safety(data.user_id, gate["reason"], data.message)
        return {"reply": gate["redirect"], "source": "safety", "mode": data.mode, "blocked": True}

    ctx = {
        "name": data.name or "buddy",
        "interests": data.interests or [],
        "language": data.language or "hinglish",
        "tone": data.tone or "fun",
        "age_group": data.age_group or "9-12",
    }
    if data.user_id:
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE id=?", (data.user_id,)).fetchone()
        finally:
            conn.close()
        if row:
            ctx.update({
                "name": row["name"],
                "interests": jload(row["interests"], []),
                "language": row["language"],
                "tone": row["tone"],
                "age_group": row["age_group"],
            })
    if data.current_topic:
        ctx["recent_learning"] = data.current_topic
    result = mentor_reply(data.message, ctx, mode=data.mode, history=data.history)
    safe_reply = safety.sanitize_output(result["reply"])  # scrub model output
    return {"reply": safe_reply, "source": result["source"], "mode": data.mode, "blocked": False}
