# wolio.ai — Play-to-Learn AI Universe for Kids

A premium, AI-driven learning app where kids don't study — they play, explore,
and become the hero, and learning happens automatically. FastAPI backend that
also serves a no-framework single-page web app.

## 🚀 Deploy your own (free) — one click

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kumudsahu/wolio.ai)

Clicking the button opens Render, asks you to sign in with GitHub and approve,
then deploys automatically using `render.yaml`. You get a public link like
`https://wolio-ai.onrender.com` to share. Pushes to `main` auto-redeploy.

Full options (Railway, Fly, local tunnel) are in **[DEPLOY.md](DEPLOY.md)**.

## 👋 Try the demo

1. Open the link → **Start my universe**
2. Enter **any email** → on the code screen the dev code **`123456`** is pre-filled → **Verify**
3. Complete the quick setup and explore. (Returning emails log back in.)

## 🧩 What's inside

| Area | Highlights |
|------|-----------|
| Onboarding | name → age → language → interests → behavioural mini-test → avatar → mentor |
| Homepage | AI hero recommendation, continue, worlds, quick-learn, daily quests, memory shortcut |
| Missions | Story → Exploration → Game → Quiz → AI explanation → Reward → Memory save |
| Memory | year/month timeline, search-your-brain, revision modes, memory strength, badges |
| Rewards | XP, coin economy, level tiers, achievements, avatar shop, confetti |
| Parent | skill analytics, AI Learning DNA, goals, screen controls, multi-child, premium |
| Platform | safety layer, admin analytics (`/admin`), rate limiting, tests + CI |
| Themes | 6 swappable themes (Cosmic, Comic, Candy, Ocean, Jungle, Neon) — full restyle |

Architecture & production notes: **[ARCHITECTURE.md](ARCHITECTURE.md)**

## 🛠️ Run locally

```bash
cd backend
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --port 8010 --reload
# app:   http://localhost:8010
# admin: http://localhost:8010/admin   (key: wolio-admin)
./.venv/bin/python -m pytest -q   # tests
```
