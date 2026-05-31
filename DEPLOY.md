# Deploying wolio.ai (get a shareable link)

The app is a single FastAPI service (`backend/`) that serves both the API and
the web app. Any Python host works. Below is the easiest free option.

## Option A — Render (free, ~2 minutes, permanent link)

1. Go to <https://render.com> and sign up (free; "Sign in with GitHub").
2. Click **New + → Blueprint**.
3. Connect the GitHub repo **kumudsahu/wolio.ai** and pick the `main` branch.
4. Render reads `render.yaml` and pre-fills everything → click **Apply**.
5. Wait for the build (~1–2 min). You'll get a public URL like
   `https://wolio-ai.onrender.com` — **share that link**.

If you'd rather not use the blueprint: New + → **Web Service** → connect the
repo → set **Root Directory** = `backend`, **Build** = `pip install -r
requirements.txt`, **Start** = `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

> Free-tier notes:
> - The service **sleeps after ~15 min idle**; the first hit then takes ~30s to wake.
> - Storage is **ephemeral** — the SQLite DB resets on each deploy/restart. Fine
>   for a "try it" demo. For persistence add a Render Disk, or move to Postgres
>   (see ARCHITECTURE.md).
> - To turn off the dev master login code, set env `DEMO_AUTH_CODE` = "" (empty).

## Option B — Railway (free trial)

New Project → Deploy from GitHub repo → set root to `backend` → it detects the
Dockerfile / Procfile → deploy → grab the generated domain.

## Option C — Fly.io / Cloud Run (Docker)

`backend/Dockerfile` is ready: `fly launch` (or `gcloud run deploy --source .`)
from the `backend/` directory.

## Option D — Instant temporary link from your laptop (no signup)

While the app runs locally (`cd backend && ./.venv/bin/python -m uvicorn
app.main:app --port 8010`), expose it with a tunnel:

```bash
# Cloudflare quick tunnel (anonymous, no account):
brew install cloudflared          # or download from cloudflare's site
cloudflared tunnel --url http://localhost:8010
# → prints a public https://<random>.trycloudflare.com link to share
```

This link lives only while your laptop and the tunnel are running — good for a
quick "look at this", not for a stable demo. Use Option A for that.

## Login for testers
Open the link → enter **any email** → on the code screen the dev code
**`123456`** is pre-filled → **Verify**. (Each new email starts a fresh child;
returning emails log back in.)
