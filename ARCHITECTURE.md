# wolio.ai — Platform Architecture (Step 7)

This document maps the **production platform design** (Step 7 spec) to what is
built in this repo today, and what scales it to 1M users. It's deliberately
honest about what is *implemented* vs *designed/stubbed*, so the team knows
exactly what to build next.

---

## 7.1–7.3 System map & services

```
Client (SPA / Flutter) → API Gateway → Core Services → AI Layer → Content Engine → DBs → Analytics → Admin
```

**Today (modular monolith)** — one FastAPI app, cleanly split by router so each
maps 1:1 to a future microservice. Extract to separate services when load demands.

| Spec service        | Module today                          | Extract to |
|---------------------|---------------------------------------|------------|
| User Service        | `routers/onboarding.py`               | users-svc |
| Learning Service    | `routers/worlds.py`, `mission.py`     | learning-svc |
| Memory Service      | `routers/timeline.py`                 | memory-svc |
| Gamification Service| `economy.py`, `routers/rewards.py`    | gamification-svc |
| Notification Service| `brain.notifications`, parent notifs  | notify-svc |
| Billing Service     | `routers/parent.py` (billing/*)       | billing-svc |
| AI Layer            | `brain.py` (recommend/tutor/memory)   | ai-svc |
| Content Engine      | `content.py` (JSON playbooks)         | content-svc + CMS |
| Admin/Analytics     | `routers/admin.py`, `/admin`          | internal-tools |

## 7.2 API Gateway — **implemented**
- Single FastAPI entry point; all feature APIs under `/api/*`.
- `platform_mw` middleware adds **`X-Process-Time-ms`** to every response and a
  per-IP **rate limit** (240 req/60s on `/api/*` → HTTP 429).
- **Auth:** app entry uses **email + 6-digit code** sign-in (`/api/auth/send-code`
  + `/api/auth/verify`); returning emails log straight in. Codes are in-memory +
  returned for the demo. Parent zone is separately PIN-gated.
- **Prod TODO:** email the code via a mail service (don't return it), hash +
  TTL the codes, JWT/refresh tokens (client currently holds `user_id` in
  localStorage), per-route quotas, an edge gateway (Kong/APIGW).

## 7.4 AI Layer — **implemented (rule-based) + LLM-ready**
- `brain.recommend_action` (homepage hero / next mission / revision) from
  recent activity, weak topics, interests, time-of-day.
- `brain.mentor_reply` tutor: rule-based offline, upgrades to OpenAI when
  `OPENAI_API_KEY` is set. Memory intelligence = spaced-repetition decay in
  `timeline.py` + re-explain via the mentor.
- **Guardrails:** `safety.py` screens input and scrubs output (see 7.10).
- **Prod TODO:** prompt cache, conversation summary store, multi-provider.

## 7.5 Content Engine — **JSON-driven, CMS designed**
- All learning content is data: `content.PLAYBOOKS` (story/exploration/game/
  quiz/explanation per mission) + `brain.WORLDS` (worlds→chapters→missions).
  Any mission without an authored playbook gets a generated fallback.
- `/admin` shows a **content catalog + authored-coverage health**.
- **Prod TODO:** an Admin Content Studio (CRUD, asset upload, A/B tests,
  versioning) writing to a `content` collection; today content ships in code.

## 7.6 Databases — **SQLite today, designed for managed scale**
- Tables: `users, concepts, events, daily_quests, revision_logs, ledger,
  achievements, parents`. `concepts.keywords` powers "Search your brain".
- DB path is env-overridable (`WOLIO_DB`) so tests/staging are isolated.
- **Prod TODO:** managed Postgres or Firestore/Mongo for primary data;
  OpenSearch/Elastic for full-text search; a warehouse (BigQuery) for analytics.

## 7.7 Data pipeline — **implemented (event log)**
- Every meaningful action writes an `events` row (`mission`, `revision`,
  `quick_learn`, `safety_block`, …) + `ledger` for XP/coins. These power
  personalization, parent insights, daily quests, and the admin analytics.
- **Prod TODO:** push events through a queue (Kafka/PubSub) → stream processor
  → warehouse, instead of querying the operational DB directly.

## 7.8 Notifications — **in-app implemented**
- Student nudges (`brain.notifications`: streak risk, revision due, unlocks) and
  parent updates (`parent._parent_notifications`).
- **Prod TODO:** push (FCM/APNs) + parent email, a scheduler (cron/Cloud
  Scheduler) for time-based revision reminders, priority/no-spam rules.

## 7.9 Billing — **mock implemented, gateway-ready**
- `parents.plan/status/trial_ends/renewal_date`; endpoints: `billing`,
  `upgrade`, `trial` (14-day), `cancel`. Plans: Free / Premium ₹8k / Premium+.
- **Prod TODO:** Razorpay (India) + Stripe (global) webhooks, invoices,
  auto-renew. No real charges happen today.

## 7.10 Safety & child protection — **implemented (multi-layer)**
The **Child-Safe AI Architecture** — a *guided / walled-garden* companion, not
an open chatbot. Pipeline: `input → INPUT FILTER → AI → OUTPUT FILTER → reply`.
- **Layer 1 input filter** (`safety.classify_input`): categorized blocks
  (self-harm, violence, sexual, drugs, gambling, hate, contact/PII) → refuse +
  positive redirect; **emotional distress** → gentle support that points to a
  trusted adult; **sensitive-but-educational** (war/death/…) → allowed but
  answered gently & age-appropriately; **parent-restricted topics** → redirect.
- **Layer 2 output filter** (`safety.sanitize_output`): strips links/emails/
  phones, and **blocks dependency/manipulation/isolation phrases** ("I'm your
  only friend", "don't tell your parents", "I love you", "keep this secret").
- **Layer 3 kid-safe personality** (`safety.system_prompt`): hard rules
  (encourage curiosity, never form dependency, never isolate from
  parents/friends, no adult/unsafe topics) + **age-based styling**
  (3-5 playful → 16-18 scientific) + walled-garden scope.
- **Parent safety layer**: dashboard shows daily AI minutes, topics discussed,
  and blocked attempts by category; parents can **restrict topics**.
- **Healthy usage**: mentor nudges an "adventure break" after a long session.
- Events logged: `ai_chat` (topic only, never raw text), `safety_block`,
  `safety_emotional` → surfaced on `/admin` and the parent panel.
- **Prod TODO:** add a moderation API (OpenAI/Perspective) as the outer layer,
  a human review queue, curated knowledge base (no open web), and COPPA/GDPR-K
  compliance processes.

## 7.11 Analytics dashboard — **implemented** (`/admin`)
- DAU/WAU, D1 retention, sessions, engagement funnel, event mix, monetization
  (conversion), safety blocks, content coverage. Guarded by `ADMIN_KEY`.
- **Prod TODO:** Mixpanel/Firebase for cohort/funnel depth.

## 7.12 Performance & scaling
- Targets: app load < 2s, core API < 300ms (observed single-digit ms locally
  via `X-Process-Time-ms`). SPA lazy-renders per screen; static served via CDN
  in prod.
- **Prod TODO:** Redis cache for homepage config & hot reads, CDN for assets,
  horizontal scaling once services are extracted.

## 7.13 Testing — **implemented**
- `backend/tests/` (pytest + TestClient) runs the whole API against an isolated
  temp DB: health, onboarding→homepage, mission rewards, search, shop tier
  gating, achievements, **safety block/allow**, parent dashboard + DNA gating,
  billing, admin auth, content coverage. `pytest -q` → 12 passing.
- **Prod TODO:** UI/E2E tests, AI-output validation suite, content QA.

## 7.14 Deployment pipeline — **implemented (CI)**
- `.github/workflows/ci.yml` installs deps and runs the test suite on every
  push/PR to `main` (Dev → CI). 
- **Prod TODO:** staging deploy + QA gate + production deploy (containerize,
  deploy to Cloud Run / Fly / ECS).

---

## Run it

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --port 8010 --reload   # app at /
./.venv/bin/python -m pytest -q                                   # tests
# admin console: http://localhost:8010/admin   (key: wolio-admin / ADMIN_KEY env)
```
