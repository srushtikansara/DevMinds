# DevMind — Cross-AI Developer Intelligence Platform

> A full-stack platform that transforms AI-assisted developer interactions into persistent knowledge, developer intelligence, career tooling, and agentic reasoning — all built and validated on real, live data.

---

## Overview

Modern developers use multiple AI tools — Claude Code, Codex, Cursor, Antigravity, and more — throughout their development workflow. These interactions remain fragmented: each tool remembers nothing beyond its own session, so context, decisions, and learning are lost the moment a conversation ends.

**DevMind** solves this by automatically capturing real sessions from your AI coding tools, extracting meaningful developer events, building long-term memory, tracking technical skills, and turning that history into concrete outcomes: personalized recommendations, an AI-tailored resume for every real job you consider, and agentic reasoning that makes genuine decisions over your real data.

---

## What's actually working (validated on real data)

### 1. Automatic capture — four connectors, fully working
- **Claude Code** — reads local `.jsonl` session files
- **Codex** — reads local `.jsonl` session files (filters reasoning/tool-call noise)
- **Cursor** — reads its local SQLite database (`state.vscdb`), resolves composer headers to bubble records
- **Antigravity IDE** — reads local JSONL transcripts (`transcript.jsonl`)

Each connector parses real session data end to end, filtering internal bookkeeping and keeping only genuine conversation turns.

### 2. The core pipeline — six automatic stages
Uploading a session triggers this chain automatically, no manual steps required:

```
Upload → Parse → Extract Events (Gemini) → Memory Engine → Skill Tracking → Developer Profile → Recommendations (Gemini)
```

- **Parse** — turns raw payloads into structured conversation turns
- **Extract Events** — Gemini identifies distinct debugging/learning/implementation/architecture-decision events
- **Memory Engine** — embeds each event (Gemini embeddings + ChromaDB), merges into existing memory or creates new memory based on a strict 0.92 similarity threshold
- **Skill Tracking** — rolls events into per-skill proficiency scores using a diminishing-returns formula
- **Developer Profile** — rebuilds a per-user summary (top skills + recent highlights) after every session
- **Recommendations** — Gemini reasons across the user's full skill combination to suggest genuinely relevant next technologies

### 3. Semantic memory search
`GET /memories/search?q=...` — ask "have I solved this before?" in plain language. Embeds the query, searches ChromaDB, blends semantic similarity with memory importance for ranking.

### 4. Weekly reports
Aggregates the current week's memories, active skills, and open recommendations into a single summary, stored per `(user, week_start)`.

### 5. Authentication
Every endpoint and every connector requires a real API key (`Authorization: Bearer <key>`), hashed and checked against the user record.

### 6. Career Intelligence — complete, real human-in-the-loop workflow
- **Resume generation** — converts real skill/memory data plus structured personal info (contact, education, multiple roles/projects) into professional, ATS-oriented resume content via Gemini, rendered as a downloadable `.docx`.
- **Resume upload** — accepts an existing PDF/DOCX, extracts text (`pdfplumber`/`python-docx`), stores it as an alternate base for tailoring.
- **Job matching** — real job postings via Apify's LinkedIn scraper (per team direction, scrapes only public, no-login pages) with Himalayas as a free, unlimited fallback source, behind a common swappable interface.
- **Batched AI fit-scoring** — scores an entire batch of jobs in a single Gemini call (not one call per job), directly addressing daily quota constraints.
- **The full HITL loop, in the UI**: browse ranked matches → **Prepare** (tailors a resume specifically for that job, with an honest gap analysis) → **Reject** (never shown again) → **Mark as applied** (only enabled after preparing) → **Applied tab** (a permanent record of everything actually applied to). DevMind never submits an application on the user's behalf.
- **`review_matches.py`** — an interactive terminal script that walks through every match one at a time with a genuine y/n prompt, for a fully manual review session.

### 7. Agentic reasoning — LangGraph
Two working agents demonstrating real, conditional decision-making over live data (not a fixed script):

- **`career_agent.py`** — fetches a real job recommendation → branches on fit_score (≥0.4 researches the company via live web search and tailors a resume; below skips) → returns a full decision trail.
- **`learning_agent.py`** — fetches a real skill's tracked signal_count → branches on whether it's a brand-new skill or one with existing signal → searches related memories → generates a mentorship-style learning plan referencing the user's actual past work → checks live job-market demand for that skill.

Both are wrapped as Celery tasks and automatically triggered on the single best new recommendation after `find_job_matches` / `generate_recommendation` run, keeping Gemini usage bounded.

**Company research uses Tavily**, not Gemini's built-in Google Search grounding — grounding requires a billed Google Cloud project even to access its free monthly allowance; Tavily is a genuinely free, no-card API purpose-built for AI agents and is the default search tool in the LangChain/LangGraph ecosystem.

### 8. MCP server — four AI clients
`mcp_server.py` exposes `get_developer_profile`, `search_memories`, `get_recommendations`, and `get_career_matches` as tools any MCP-compatible AI client can call directly in conversation.

- ✅ **Claude Desktop** — verified working with real data
- ✅ **Cursor** — verified working with real data
- ✅ **Antigravity IDE** — verified working with real data
- ⏸️ **Codex** — correctly configured via the standalone CLI (the VS Code extension has a known, documented MCP-detection bug); currently blocked by an unrelated Codex account usage limit, unrelated to DevMind

### 9. Frontend dashboard — Next.js + React
A real, six-page dashboard, all connected to live backend data via a CORS-enabled API:

- **Profile** — real skill proficiency bars, activity stats, recent highlights
- **Career** — tabbed Matches / Applied view; ranked job cards with a live fit-score bar; a modal showing the full tailored resume, highlighted skills, and honest gap notes; direct in-card actions (Prepare, Reject, Mark as applied) that reflect real backend state, not local-only UI state
- **Resumes** — upload (PDF/DOCX), a dynamic multi-entry form (add unlimited education and experience/project entries) to generate a new resume, a filtered list showing only browsable resumes (tailored, job-specific versions are intentionally kept out of this list and are only shown at the moment they're created)
- **Skills** — a real bar chart of tracked proficiency, plus current recommendations
- **Reports** — loads any week's stored weekly report by date

### 10. Automation
- **Nightly** (`run_all_connectors.bat`, via Windows Task Scheduler) — starts Docker, the API, and Celery, then runs all four connectors, capturing any new real sessions unattended.
- **Weekly** (`run_career_matching.bat`, separate schedule) — deliberately kept apart from the nightly sync to conserve Gemini/Apify quota.

---

## Architecture

- **PostgreSQL** — primary store: users, connectors, sessions, conversations, developer events, memories, embeddings (pointers), skill signals, skills, developer profiles, recommendations, weekly reports, resumes, job postings, career recommendations
- **ChromaDB** — vector store for memory embeddings, enabling semantic search and merge/create decisions
- **Redis + Celery** — background task queue; every pipeline stage after upload, plus both LangGraph agents, run as independent Celery tasks
- **Gemini (`gemini-3.5-flash`)** — event extraction, embeddings, skill recommendations, resume generation/tailoring, batched job fit-scoring
- **LangGraph** — agentic orchestration layer, sitting alongside (not replacing) the core Celery pipeline; both call into the same shared Postgres/ChromaDB/Gemini layer
- **Tavily** — free web search API for the career agent's live company research step
- **FastAPI** — REST API, CORS-enabled for the frontend, all endpoints behind API-key authentication
- **Next.js + React + Tailwind** — the dashboard

### Why Gemini instead of a local model
A documented experiment (Ollama, multiple local models) found that local models reliably followed the JSON schema on short conversations but became unreliable on long, real conversations. Gemini handled the same real data correctly on the first attempt.

### A real, recurring constraint: the Gemini free tier
The free tier's 20-requests/day limit has been hit repeatedly during active development — confirmed with real usage-dashboard data. Mitigations built in response: batched fit-scoring (one call for an entire job batch instead of one per job), a retry decorator for transient `503` overloads, bounding automatic agent triggers to the single best result, and a secondary Gemini project/key for testing continuity. This is an open, ongoing conversation with the team about moving to a paid tier.

### Why Apify (LinkedIn) and Himalayas together for job data
LinkedIn, Indeed, Naukri, Internshala, and Glassdoor were all confirmed to have **no free official API** for job/company data — only paid or ToS-risky scraping options. Per team direction, Apify's LinkedIn scraper (public pages only, no login, no personal account risk) is used as the primary job source, with Himalayas (a genuinely free, unlimited, official API) as a zero-cost fallback — both behind the same `search_jobs()` interface, so switching or adding sources requires no changes to the worker itself.

### A note on "why isn't this chat captured?"
Connectors work because Claude Code, Codex, Cursor, and Antigravity IDE each write a local session file automatically. A conversation in a web/desktop chat interface (Claude Desktop's regular chat, ChatGPT, or a claude.ai conversation) produces no local file — there is nothing for a connector to read. This is a structural limitation, not a missing feature.

---

## Running locally

### Backend

```bash
cp .env.example .env      # DATABASE_URL, GEMINI_API_KEY, DEVMIND_API_KEY, APIFY_API_TOKEN, TAVILY_API_KEY
docker compose up -d postgres redis chromadb
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

In a separate terminal:
```bash
celery -A app.infrastructure.queue.celery_app worker --loglevel=info --pool=solo
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. Requires `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_KEY=<your DevMind API key>
```

### Running all connectors automatically

Instead of running each connector individually, use the single automation script — it starts Docker, the API, Celery, and then runs all four connectors in sequence, uploading any new sessions found.

```powershell
cd DevMind
.\backend\run_all_connectors.bat
```

Safe to run repeatedly — connectors are idempotent, so already-uploaded sessions are simply skipped.

**What it does:**
1. Starts Docker containers (PostgreSQL, Redis, ChromaDB)
2. Starts the FastAPI backend
3. Starts the Celery worker
4. Runs each connector against its real local session files:
   - Claude Code — `~/.claude/projects/`
   - Codex — `~/.codex/sessions/`
   - Cursor — local SQLite DB (`state.vscdb`)
   - Antigravity IDE — `~/.gemini/antigravity-ide/brain/`

This script is also registered as a nightly Windows Task Scheduler job (`DevMind Nightly Sync`) for fully unattended capture.

**Verifying it worked:**
```powershell
docker compose exec postgres psql -U devmind -d devmind -c "SELECT session_upload_id, status, ingested_at FROM sessions ORDER BY ingested_at DESC LIMIT 5;"
```

### Testing the LangGraph agents directly

```bash
cd backend
python test_career_agent.py
python test_agent.py
```

### Interactive HITL review

```bash
python review_matches.py
```

---

## Project structure

```
DevMind/
├── backend/
│   ├── app/
│   │   ├── infrastructure/
│   │   │   ├── db/models/         # SQLAlchemy models, one file per table
│   │   │   ├── llm/                # Gemini provider: events, embeddings, recommendations, resume + tailoring
│   │   │   ├── embeddings/         # Gemini embedding wrapper
│   │   │   ├── vectorstore/        # ChromaDB client wrapper
│   │   │   ├── documents/          # Resume parsing (upload) and .docx building (generation)
│   │   │   ├── jobs/               # Job-source clients (Apify, Himalayas) behind a common interface
│   │   │   └── queue/              # Celery app configuration
│   │   └── interfaces/http/        # FastAPI router, auth dependency, CORS
│   ├── agents/
│   │   ├── career_agent.py         # LangGraph: fit-based branching, Tavily research, resume tailoring
│   │   └── learning_agent.py       # LangGraph: skill-signal branching, mentorship-style plans
│   ├── workers/                    # One Celery task per pipeline stage, plus agent_worker.py
│   ├── alembic/versions/           # Migration history
│   ├── mcp_server.py                # MCP server: 4 tools, works across Claude Desktop/Cursor/Antigravity/Codex
│   ├── run_all_connectors.bat       # Nightly automation entry point
│   └── run_career_matching.bat      # Weekly automation entry point
├── frontend/
│   └── app/
│       ├── page.tsx                # Profile
│       ├── career/page.tsx         # Career (Matches / Applied tabs)
│       ├── resumes/page.tsx        # Resumes (upload, generate, download)
│       ├── skills/page.tsx         # Skills chart + recommendations
│       ├── reports/page.tsx        # Weekly reports
│       └── components/Nav.tsx
├── connectors/
│   ├── claude-code-connector/
│   ├── codex-connector/
│   ├── cursor-connector/
│   └── antigravity-connector/
└── docs/
    └── devmind-mvp-plan.md         # Full scope, schema, API contracts, and investigation log
```

---

## Status

**Complete and verified end to end, with real data:** capture (4 connectors + nightly automation), the full 6-stage pipeline, semantic search, weekly reports, authentication, Career Intelligence (generation, upload, matching, tailoring, full HITL loop), 2 LangGraph agents with live web research, MCP across 3 of 4 target clients, and a 6-page working frontend dashboard.

**Open, ongoing:** Codex MCP (blocked by an account-level usage limit, unrelated to DevMind, self-resolving); a team discussion on moving Gemini/Apify to paid tiers given repeated, evidenced free-tier exhaustion during active development.

**Deferred, documented, not planned near-term:** ChatGPT and regular Claude Desktop chat connectors (both cloud-only, no local file to read); real JWT-based multi-user authentication (current single-user API key is sufficient for now); public deployment (currently local-only).

---

## License

This project is intended for educational, research, and portfolio purposes. The architecture is designed with production-ready principles and can be extended into a scalable, multi-user SaaS platform.