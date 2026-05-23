# CrunchTime — Project Plan

## Overview

**What it is:** A real-time alerting platform that monitors live NBA and MLB games and notifies users when game conditions match user-defined alert rules (close 4th quarters, late-inning one-run games, walk-off scenarios, comeback alerts).

**Why it exists:** No existing app reliably notifies sports fans when a game enters its most exciting moments. ESPN/Yahoo do crude "close game" alerts but they fire too early, too often, or too late. NFL RedZone solves this for TV but not as a notification product, and only for one sport.

**Target user:** Sports fans who want to tune in only when a game gets interesting, without watching every minute of every game.

---

## Goals

### Primary goal
Ship a working, deployed product with real users (even if just 10-50 friends/X followers) within 4-5 weekends.

### Secondary goals
- Build a portfolio-grade SWE project demonstrating: real-time systems, external API integration, polling efficiency, push notifications, sport-specific rules engine, deduplication, and latency budgets
- Get experience marketing in public on X
- Produce a clean GitHub repo with README, architecture diagram, and demo gif that can be linked from a resume

### Non-goals (explicitly out of scope for v1)
- Multi-sport beyond NBA + MLB (NFL/NHL/soccer come later if there's demand)
- iOS/Android native apps (PWA + web push only)
- Authentication beyond email-based signup (no OAuth, no social login)
- Monetization (premium tier comes only if usage justifies it)
- Real-time stream processing infrastructure (Kafka, etc.) — polling is fine at this scale
- Mobile-first UI polish (responsive web is enough)
- Multi-tenancy or team accounts

---

## Architecture
┌─────────────────┐
│  React/Next.js  │ ◄──── User browses, signs up, sets preferences
│   Frontend      │
└────────┬────────┘
│ HTTPS
▼
┌─────────────────┐         ┌──────────────────┐
│   FastAPI       │ ◄─────► │   PostgreSQL     │ (users, prefs, alert history)
│   Backend       │         └──────────────────┘
└────────┬────────┘
│
▼
┌─────────────────┐         ┌──────────────────┐
│   Redis         │ ◄─────► │  Polling Worker  │ (Python process)
│   (live state,  │         │                  │
│    dedup keys,  │         └────────┬─────────┘
│    pub/sub)     │                  │
└─────────────────┘                  ▼
┌─────────────────────┐
│  External APIs:     │
│  - MLB Stats API    │
│  - NBA live endpts  │
└─────────────────────┘
│
▼
┌─────────────────────┐
│  Rules Engine       │
│  (sport-specific    │
│   tension logic)    │
└────────┬────────────┘
│
▼
┌─────────────────────┐
│ Notification        │
│ Dispatcher          │
│ (Web Push API)      │
└────────┬────────────┘
│
▼
┌─────────────────────┐
│  User's Browser/    │
│  PWA (push notif)   │
└─────────────────────┘

### Core components

1. **Polling Worker** — single Python process that polls MLB Stats API and NBA endpoints for live games. Maintains an in-memory list of active games, adapts polling cadence based on game state (every 60s for games not in tense window, every 15s when entering tense window).

2. **Rules Engine** — sport-specific functions that take a game state object and return whether the game is currently "tense." Examples:
 - NBA: 4th quarter, < 5:00 remaining, score differential ≤ 6
 - MLB: 8th inning+, score differential ≤ 2 runs, OR 9th inning with runners on for walk-off
 - Future-proofed for user-configurable rules per sport

3. **Deduplication Layer** — Redis-based. Stores `(user_id, game_id, alert_type)` keys with TTL. Prevents re-notifying the same user about the same game's same condition within a window.

4. **Notification Dispatcher** — takes (user_id, game_id, alert_payload), looks up the user's push subscription, fires via Web Push protocol. Handles failures with retry.

5. **Frontend** — Next.js. Landing page, signup, preferences (which sports, which teams, alert rules), and a history page showing past alerts received.

6. **Postgres schema (initial):**
 - `users` (id, email, push_subscription_json, created_at)
 - `user_preferences` (user_id, sport, alert_rules_json)
 - `alert_history` (id, user_id, game_id, sport, alert_type, fired_at, game_state_snapshot)

---

## Tech stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js (TypeScript) | One codebase for SSR + API routes if needed; React skills demo |
| Backend | FastAPI (Python) | Fast to build; Python aligns with worker code |
| Worker | Python (asyncio) | Async polling; concurrent game monitoring |
| Database | PostgreSQL | User data, preferences, alert history |
| Cache / Pub-Sub | Redis | Live game state, dedup keys, optional pub/sub |
| Push Notifications | Web Push API (pywebpush lib) | Free, works in Chrome/Firefox/Edge/Safari (iOS 16.4+) |
| Container | Docker + Docker Compose | Multi-service local dev, single deploy artifact |
| Hosting | Fly.io or Railway | Cheap, supports persistent services (worker), Postgres + Redis add-ons |
| External APIs | MLB Stats API (free, no key), nba_api Python package (free, scrapes NBA.com endpoints) | Zero API cost; only constraint is rate limits |

### Why these external APIs

- **MLB:** `statsapi.mlb.com` — official MLB API, free, no key. Same backend that powers MLB.com and the MLB app. Endpoint `/api/v1.1/game/{gamePk}/feed/live` gives full live state.
- **NBA:** `nba_api` Python package (swar/nba_api on GitHub) — wraps NBA.com's unofficial endpoints. Free, no key. Needs proper headers (User-Agent spoofing). Fallback: ESPN's hidden public endpoints (`site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`).

---

## Roadmap

### Weekend 1 — Core engine (CLI only, no UI, no notifications)

**Goal:** By end of weekend, run `python run.py` and see correct "tense window" detection printed to console for any live NBA or MLB game.

- [ ] Set up repo: `crunchtime/` with `worker/`, `backend/`, `frontend/`, `docker-compose.yml`
- [ ] Implement MLB Stats API client (simple Python module, `requests.get`)
- [ ] Implement NBA client using `nba_api` package
- [ ] Implement `is_tense_nba(game_state)` function with rules from spec
- [ ] Implement `is_tense_mlb(game_state)` function with rules from spec
- [ ] Implement polling worker loop (async): for each live game, check tense state, print transitions
- [ ] Manual test: leave it running during a live game night, verify correct detection
- [ ] Write unit tests for rules engine with mock game states

**Deliverable:** A working CLI that prints correct alerts during real games.

### Weekend 2 — Notifications + multi-sport reliability

**Goal:** By end of weekend, receive a push notification in your browser when a real game enters a tense window.

- [ ] Set up FastAPI backend skeleton with health check
- [ ] Set up Postgres locally via Docker Compose
- [ ] Implement user signup endpoint (email + push subscription JSON from browser)
- [ ] Implement Postgres schema (users, preferences, alert_history)
- [ ] Implement Redis dedup layer (keys with TTL)
- [ ] Implement Web Push integration (`pywebpush`)
- [ ] Wire polling worker → rules engine → dispatcher → push notification
- [ ] Build minimal HTML page to subscribe a user (no styling, just functionality)
- [ ] Test end-to-end: sign up in browser, leave a game running, receive a real push

**Deliverable:** Receive a push notification on your phone (PWA) or laptop browser when a real game gets close.

### Weekend 3 — Real frontend + user preferences

**Goal:** By end of weekend, a stranger could land on the site, sign up, set preferences, and start receiving alerts.

- [ ] Build Next.js frontend: landing page, signup flow, preferences page, alert history page
- [ ] User preferences: which sports (NBA/MLB), which teams (optional filter), alert types (close game, walk-off, comeback)
- [ ] Alert history page: list of alerts received with final game scores
- [ ] Backend endpoints for preferences CRUD
- [ ] Worker respects user preferences when dispatching alerts
- [ ] Basic visual polish: pick a clean design (use a Tailwind UI template if needed)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

**Deliverable:** A complete product that someone other than you could use end-to-end.

### Weekend 4 — DevOps + deploy + polish

**Goal:** By end of weekend, the product is live on the internet with a public URL.

- [ ] Finalize `docker-compose.yml` for local dev
- [ ] Set up GitHub Actions CI (lint, tests, build images)
- [ ] Deploy to Fly.io: backend, worker, Postgres, Redis
- [ ] Configure domain (custom subdomain or `.fly.dev`)
- [ ] Set up basic monitoring (Fly's built-in metrics + a `/health` endpoint hit by uptime monitor)
- [ ] Handle gotchas:
 - Rate limiting on NBA API (rotate User-Agents, add jitter)
 - Worker restart safety (idempotent, no duplicate alerts on restart)
 - Web Push key generation and storage
- [ ] Write README with architecture diagram, motivation, setup instructions
- [ ] Record demo gif (browser sign-up → simulated alert)
- [ ] Pin repo to GitHub profile

**Deliverable:** Live URL someone can sign up on. Public GitHub repo. Demo gif on README.

### Weekend 5 — Launch + iterate

**Goal:** Get the first 20-50 users.

- [ ] Write a "build-in-public" thread on X covering the build journey
- [ ] Post launch tweet with demo gif
- [ ] Submit to relevant subreddits (r/nba, r/baseball, r/SideProject)
- [ ] Add to Product Hunt (optional, low priority)
- [ ] Monitor for first-day bugs (notifications not firing, dedup issues, etc.)
- [ ] Iterate based on early feedback

**Deliverable:** First 20+ users, first batch of feedback, project ready to put on resume with real metrics.

---

## Risks and mitigation

### External API risks
- **NBA blocks scrapers:** Rotate User-Agents, randomize polling intervals with jitter, respect implicit rate limits. Have ESPN endpoints ready as backup.
- **MLB Stats API changes:** Unlikely (it's their official API), but monitor for breaking changes.
- **Game schedule data:** Need to know which games are live; cache the daily schedule at start of day to reduce calls.

### Notification reliability
- **Push notifications drop:** Web Push doesn't guarantee delivery. Log every send attempt, build a feedback loop with users on missed alerts.
- **iOS Safari quirks:** iOS 16.4+ supports Web Push but only when the site is installed as a PWA. Document this clearly in onboarding.
- **Worker crash during a comeback:** Restart safety. Use a process manager (systemd, or Fly's restart policy). On restart, re-fetch live games and pick up where left off.

### Latency risk
- **Goal: <30 seconds from game-state-change to user notification.** Test this explicitly. If polling cadence is 15s + API call takes 2s + dispatcher takes 5s = ~22s. Acceptable.

### Cost risk
- **Total cost target: <$20/month.** Fly.io free tier covers worker + small Postgres. Redis cheap. APIs free.

### Burnout risk
- **5 weekends is real time.** Stick to scope cuts. Resist scope creep. Multi-sport, mobile apps, monetization all wait until v1 is live.

---

## Success criteria

### Minimum viable success (after Weekend 4)
- Live URL anyone can use
- Public GitHub repo with README and demo gif
- At least 1 real alert successfully delivered during a real game

### Resume-grade success (after Weekend 5)
- 20+ real users signed up
- 50+ alerts delivered in first week
- Clean writeup on GitHub
- Architecture diagram in README

### Bonus / stretch
- 100+ users
- Featured in a sports-X account's tweet
- Real X follower growth from build-in-public
- Expand to NFL, NHL, soccer

---

## Open questions

- Should alerts include a preview image/score graphic, or text-only? (Text-only for v1; images later.)
- Should there be a "snooze" feature (mute alerts for 1 hour)? Add if early users ask for it.
- Premium tier idea: $5/month for custom alert rules ("only my team," "any game where the underdog is winning"). Decide after launch.
- iOS PWA installation prompts — how aggressive should we be? (Low for v1, prompt only after first successful alert.)

---

## Personal commitments

- This is my SWE-resume project. It goes on the resume the day Weekend 4 is shipped, not before.
- Weekend definitions: Saturday + Sunday, ~6-8 hours each day.
- I will not skip the "ship it live" step. The whole point is "deployed product," not "side project sitting in localhost."
- If I miss a weekend, I extend the timeline rather than cut scope.