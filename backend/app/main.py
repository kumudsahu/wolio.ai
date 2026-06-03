"""wolio.ai — Play-to-Learn AI Universe for Kids.

FastAPI serves both the API and the premium single-page web app.
Run:  ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
"""
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .db import init_db
from .routers import onboarding, worlds, timeline, mentor, home, mission, rewards, parent, admin, auth, crew

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="wolio.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 7.2/7.12 platform middleware: timing header + lightweight rate limit ---
RATE_LIMIT = 240          # requests
RATE_WINDOW = 60.0        # seconds, per client IP
_hits: dict = defaultdict(deque)


@app.middleware("http")
async def platform_mw(request: Request, call_next):
    ip = request.client.host if request.client else "anon"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if request.url.path.startswith("/api/") and len(q) >= RATE_LIMIT:
        return JSONResponse({"detail": "Too many requests — slow down a moment."}, status_code=429)
    q.append(now)

    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Process-Time-ms"] = f"{(time.monotonic() - start) * 1000:.1f}"
    return response


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "app": "wolio.ai", "version": app.version,
            "ai": bool(os.getenv("OPENAI_API_KEY"))}


app.include_router(onboarding.router)
app.include_router(worlds.router)
app.include_router(timeline.router)
app.include_router(mentor.router)
app.include_router(home.router)
app.include_router(mission.router)
app.include_router(rewards.router)
app.include_router(parent.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(crew.router)

# Static assets (css/js/img) under /static, and the SPA at /.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.api_route("/", methods=["GET", "HEAD"])
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/admin")
def admin_page():
    return FileResponse(str(STATIC_DIR / "admin.html"))
