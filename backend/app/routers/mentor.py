from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..db import get_conn, jload
from ..brain import mentor_reply

router = APIRouter(prefix="/api", tags=["mentor"])


class MentorIn(BaseModel):
    user_id: Optional[int] = None
    message: str
    mode: str = "fun"  # fun | quick | quiz
    # allow anonymous chat (e.g. during onboarding) with inline context
    name: Optional[str] = None
    interests: Optional[List[str]] = None
    language: Optional[str] = None
    tone: Optional[str] = None
    age_group: Optional[str] = None


@router.post("/mentor")
def chat(data: MentorIn):
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
    result = mentor_reply(data.message, ctx)
    return {"reply": result["reply"], "source": result["source"], "mode": data.mode}
