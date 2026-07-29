# DevMind — Cross-AI Developer Intelligence Platform

> A production-ready platform that transforms AI-assisted developer interactions into persistent knowledge, developer intelligence, and personalized learning and career insights.

---

## Overview

Modern developers use multiple AI tools — Claude Code, Codex, Cursor, Antigravity, and more — throughout their development workflow. These interactions remain fragmented: each tool remembers nothing beyond its own session, so context, decisions, and learning are lost the moment a conversation ends.

**DevMind** solves this by automatically capturing real sessions from your AI coding tools, extracting meaningful developer events, building long-term memory, tracking technical skills, and generating personalized recommendations — all without you doing anything beyond your normal work.

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
- **Recommendations** — Gemini reasons across the user's full skill combination to suggest genuinely relevant next technologies (not a hardcoded lookup table)

### 3. Semantic memory search
`GET /memories/search?q=...` — ask "have I solved this before?" in plain language. Embeds the query, searches ChromaDB, blends semantic similarity with memory importance for ranking.

### 4. Weekly reports
Aggregates the current week's memories, active skills, and open recommendations into a single summary, stored per `(user, week_start)`.

### 5. Authentication
Every endpoint and every connector requires a real API key (`Authorization: Bearer <key>`), hashed and checked against the user record — no hardcoded dev-user shortcuts remain.

### 6. Career Intelligence (in progress)
- **Resume generation** — working. Converts real skill/memory data plus structured personal info (contact, education, dated roles) into professional, ATS-oriented resume content via Gemini, rendered as a downloadable `.docx`.
- **Resume upload path** — not yet built (planned: accept an existing resume file for users who don't want auto-generation).
- **Job matching** — designed, not yet built. Real, legitimate free job-data sources identified: Himalayas, Arbeitnow, RemoteOK, Remotive (all zero-setup), Adzuna, Jooble, Careerjet, The Muse, Reed. LinkedIn, Indeed, Naukri, Internshala, and Glassdoor confirmed to have **no free official APIs** — only paid or ToS-risky scraping options exist, which this project deliberately avoids.
- **Human-in-the-loop by design** — DevMind will prepare (search, score fit, tailor resume) but never auto-submit an application. Every submission requires explicit user action.

### 7. MCP server — Claude Desktop integration
A local MCP server exposes `get_developer_profile`, `search_memories`, and `get_recommendations` as tools Claude Desktop can call directly in conversation, authenticated via the same API key. Read-only — it never writes back into DevMind.

### 8. Automation
`run_all_connectors.bat` starts Docker, the API, and Celery, then runs all four connectors against every local session file found. Scheduled nightly via Windows Task Scheduler — the entire capture pipeline runs unattended.

---

## Architecture

- **PostgreSQL** — primary store: users, connectors, sessions, conversations, developer events, memories, embeddings (pointers), skill signals, skills, developer profiles, recommendations, weekly reports, resumes, job postings, career recommendations
- **ChromaDB** — vector store for memory embeddings, enabling semantic search and merge/create decisions
- **Redis + Celery** — background task queue; every pipeline stage after upload runs as an independent, automatically-triggered Celery task
- **Gemini (`gemini-3.5-flash`)** — used for event extraction, embeddings, skill recommendations, and resume content generation, all via JSON Schema–constrained structured output
- **FastAPI** — REST API, all endpoints behind API-key authentication

### Why Gemini instead of a local model
A documented experiment (Ollama, multiple local models) found that local models reliably followed the JSON schema on short conversations but became unreliable on long, real conversations — inventing formats or returning empty results. Gemini handled the same real data correctly on the first attempt. See `docs/devmind-mvp-plan.md` for the full experiment log.

### A note on "why isn't this chat captured?"
Connectors work because Claude Code, Codex, Cursor, and Antigravity IDE each write a local session file automatically. A conversation in a web/desktop chat interface (Claude Desktop's regular chat, ChatGPT, or this conversation itself) produces no local file — there is nothing for a connector to read. This is a structural limitation, not a missing feature, and applies equally to every such interface investigated.

---

## Running locally

```bash
cp .env.example .env      # fill in real values (DATABASE_URL, GEMINI_API_KEY, DEVMIND_API_KEY, etc.)
docker compose up -d postgres redis chromadb
cd backend
alembic upgrade head       # apply all migrations
uvicorn app.main:app --reload
```

In a separate terminal, start the Celery worker:

```bash
cd backend
celery -A app.infrastructure.queue.celery_app worker --loglevel=info
```

(On Windows, add `--pool=solo` to the Celery command.)

### Running a connector manually

```bash
python connectors/claude-code-connector/upload_session.py "<path-to-jsonl>"
python connectors/codex-connector/upload_session.py "<path-to-jsonl>"
python connectors/cursor-connector/upload_session.py "<path-to-state.vscdb>"
python connectors/antigravity-connector/upload_session.py "<path-to-transcript.jsonl>"
```

### Running all connectors automatically

Instead of running each connector individually, use the single automation script — it starts Docker, the API, Celery, and then runs all four connectors (Claude Code, Codex, Cursor, Antigravity) in sequence, uploading any new sessions found.

```powershell
cd DevMind
.\backend\run_all_connectors.bat
```

This is safe to run repeatedly — connectors are idempotent, so already-uploaded sessions are simply skipped, not duplicated.

**What it does, step by step:**
1. Starts Docker containers (PostgreSQL, Redis, ChromaDB)
2. Starts the FastAPI backend (`uvicorn`)
3. Starts the Celery worker
4. Runs each connector against its real local session files:
   - Claude Code — `~/.claude/projects/`
   - Codex — `~/.codex/sessions/`
   - Cursor — local SQLite DB (`state.vscdb`)
   - Antigravity IDE — `~/.gemini/antigravity-ide/brain/`

**Automating it further:** this same script is registered as a scheduled Windows Task (`DevMind Nightly Sync`), running automatically every night via Task Scheduler — no manual step required once set up.

**Verifying it worked:**
```powershell
docker compose exec postgres psql -U devmind -d devmind -c "SELECT session_upload_id, status, ingested_at FROM sessions ORDER BY ingested_at DESC LIMIT 5;"
```
Should show recent, real session uploads with `status: parsed`.

---

## Project structure

```
DevMind/
├── backend/
│   ├── app/
│   │   ├── infrastructure/
│   │   │   ├── db/models/        # SQLAlchemy models, one file per table
│   │   │   ├── llm/               # Gemini provider: events, embeddings, recommendations, resume content
│   │   │   ├── embeddings/        # Gemini embedding wrapper
│   │   │   ├── vectorstore/       # ChromaDB client wrapper
│   │   │   ├── documents/         # Resume .docx builder
│   │   │   ├── jobs/               # Job-source clients (Himalayas, Arbeitnow, etc.)
│   │   │   └── queue/             # Celery app configuration
│   │   └── interfaces/http/       # FastAPI router, auth dependency
│   ├── workers/                   # One Celery task per pipeline stage
│   ├── alembic/versions/          # Migration history
│   ├── mcp_server.py              # MCP server for Claude Desktop
│   └── run_all_connectors.bat     # Automation entry point
├── connectors/
│   ├── claude-code-connector/
│   ├── codex-connector/
│   ├── cursor-connector/
│   └── antigravity-connector/
└── docs/
    └── devmind-mvp-plan.md        # Full scope, schema, API contracts, and investigation log
```

---

## Status

**Core platform: complete.** Capture, parsing, event extraction, memory, skill tracking, profile generation, recommendations, semantic search, weekly reports, authentication, and Claude Desktop integration are all built and validated on real data across all four connectors.

**In progress:** Career Intelligence job matching (blocked on a source decision — free-only vs. paid/enterprise LinkedIn access — pending team discussion) and the resume upload path.

**Deferred, documented, not planned near-term:** ChatGPT and regular Claude Desktop chat connectors (both are cloud-only with no local file to read — the only path is each platform's manual account data export).

---

## License

This project is intended for educational, research, and portfolio purposes. The architecture is designed with production-ready principles and can be extended into a scalable SaaS platform.