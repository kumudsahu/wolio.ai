"""Email authentication (demo) — a 6-digit code sign-in.

In production the code would be emailed (and never returned by the API) and
stored hashed with a TTL. For this demo we keep codes in memory and return the
code so it's testable without a mail service. Returning users (email already
attached to an onboarded child) log straight in and skip onboarding.
"""
import re
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn

router = APIRouter(prefix="/api/auth", tags=["auth"])

_CODES: dict = {}   # email -> code (in-memory, demo only)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailIn(BaseModel):
    email: str


@router.post("/send-code")
def send_code(data: EmailIn):
    email = data.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address")
    code = f"{random.randint(0, 999999):06d}"
    _CODES[email] = code
    # PROD: send `code` via email; do NOT return it. Demo: return for testing.
    return {"ok": True, "demo_code": code}


class VerifyIn(BaseModel):
    email: str
    code: str


@router.post("/verify")
def verify(data: VerifyIn):
    email = data.email.strip().lower()
    if _CODES.get(email) != data.code.strip():
        raise HTTPException(401, "That code isn't right (or expired). Try again.")
    _CODES.pop(email, None)
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email=? AND onboarded=1 ORDER BY id LIMIT 1", (email,)
        ).fetchone()
    finally:
        conn.close()
    return {"ok": True, "email": email, "user_id": row["id"] if row else None}
