from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..db import get_conn, jdump, jload
from ..brain import build_journey, difficulty_tier

router = APIRouter(prefix="/api", tags=["onboarding"])


class OnboardingIn(BaseModel):
    name: str
    age_group: str
    grade: Optional[str] = None
    language: str = "hinglish"
    tone: str = "fun"
    voice: bool = True
    interests: List[str] = []
    learning_style: str = "games"
    avatar: Optional[Dict[str, Any]] = None
    behavior: Optional[Dict[str, Any]] = None  # mini-test results


@router.post("/onboarding")
def complete_onboarding(data: OnboardingIn):
    if not data.name.strip():
        raise HTTPException(400, "Name is required")
    tier = difficulty_tier(data.age_group)
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO users
               (name, age_group, grade, language, tone, voice, avatar, interests,
                learning_style, difficulty_tier, onboarded, streak)
               VALUES (?,?,?,?,?,?,?,?,?,?,1,1)""",
            (data.name.strip(), data.age_group, data.grade, data.language, data.tone,
             int(data.voice), jdump(data.avatar or {}), jdump(data.interests),
             data.learning_style, tier),
        )
        user_id = cur.lastrowid
        if data.behavior:
            conn.execute(
                "INSERT INTO events (user_id, kind, payload) VALUES (?,?,?)",
                (user_id, "onboarding_behavior", jdump(data.behavior)),
            )
        conn.commit()
    finally:
        conn.close()

    journey = build_journey(data.name.strip(), data.interests, data.learning_style)
    return {"user_id": user_id, "journey": journey}


class PrefsIn(BaseModel):
    language: Optional[str] = None
    tone: Optional[str] = None
    voice: Optional[bool] = None
    avatar: Optional[Dict[str, Any]] = None


@router.patch("/me/{user_id}")
def update_prefs(user_id: int, data: PrefsIn):
    fields, params = [], []
    if data.language is not None: fields.append("language=?"); params.append(data.language)
    if data.tone is not None:     fields.append("tone=?");     params.append(data.tone)
    if data.voice is not None:    fields.append("voice=?");    params.append(int(data.voice))
    if data.avatar is not None:   fields.append("avatar=?");   params.append(jdump(data.avatar))
    if not fields:
        return {"updated": False}
    params.append(user_id)
    conn = get_conn()
    try:
        cur = conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "User not found")
    finally:
        conn.close()
    return {"updated": True}


@router.get("/me/{user_id}")
def get_me(user_id: int):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "User not found")
    u = dict(row)
    u["avatar"] = jload(u.get("avatar"), {})
    u["interests"] = jload(u.get("interests"), [])
    u["voice"] = bool(u.get("voice"))
    return u
