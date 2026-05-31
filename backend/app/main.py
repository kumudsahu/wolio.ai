"""wolio.ai — Play-to-Learn AI Universe for Kids.

FastAPI serves both the API and the premium single-page web app.
Run:  ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .db import init_db
from .routers import onboarding, worlds, timeline, mentor, home, mission, rewards

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="wolio.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "app": "wolio.ai", "ai": bool(os.getenv("OPENAI_API_KEY"))}


app.include_router(onboarding.router)
app.include_router(worlds.router)
app.include_router(timeline.router)
app.include_router(mentor.router)
app.include_router(home.router)
app.include_router(mission.router)
app.include_router(rewards.router)

# Static assets (css/js/img) under /static, and the SPA at /.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.api_route("/", methods=["GET", "HEAD"])
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
