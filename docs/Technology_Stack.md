# Technology Stack — As Built

> This document reflects the actual, implemented and tested technology stack, as it stands today. Where a decision diverges from the original plan (`17_Technology_Stack.md`), the reason is documented — each divergence was a deliberate, evidence-based choice made during development, not an oversight.

---

## Backend

### FastAPI

Purpose
- REST APIs for all DevMind functionality
- Session ingestion, memory search, career matching, resume management

Status: ✅ Implemented as planned

---

## Frontend

### Not yet built

Originally planned: Next.js + React

Status: ⏳ Deliberately deferred — built the complete backend first, dashboard is the next major phase

---

## Database

### PostgreSQL

Purpose: Store structured data

Stores (as actually implemented)
- Users, Connectors, Sessions, Conversations
- DeveloperEvents, Memories, Embeddings (pointers)
- SkillSignals, Skills, DeveloperProfiles
- Recommendations, WeeklyReports
- Resumes (generated, uploaded, and tailored)
- JobPostings, CareerRecommendations

Status: ✅ Implemented as planned, 14 real tables in production use

---

## Vector Database

### ChromaDB

Purpose: Semantic search over developer memories

Stores: Memory embeddings, used for merge/create decisions and semantic search

Status: ✅ Implemented as planned

---

## Cache / Queue

### Redis

Purpose: Celery broker

Status: ✅ Implemented as planned

---

## Background Processing

### Celery

Purpose (as actually implemented)
- Session parsing, event extraction
- Memory processing, skill tracking
- Developer profile updates, recommendations
- Weekly report generation, resume generation
- Career/job matching

Status: ✅ Implemented as planned — 10 registered tasks, chained automatically stage-to-stage

---

## AI Framework

### LangGraph

Purpose: Agentic, multi-step reasoning with real conditional branching

Implemented as a learning exercise, built on top of the existing production pipeline:
- `career_agent.py` — fetches a real job recommendation, branches on fit_score (≥0.4 searches memory and tailors a resume; below skips), demonstrating genuine conditional routing over live data
- `learning_agent.py` — fetches a real skill's signal_count, branches on whether it's a new skill or an existing one, searches related memories, generates a tailored learning plan, and checks live job-market demand for that skill

Status: ✅ Implemented — both agents tested successfully against real production data (real fit scores, real skill signal counts, real job postings)

---

## LLM

### Gemini (gemini-3.5-flash)

Used for: event extraction, embeddings-adjacent reasoning, skill recommendations, resume generation and tailoring, job fit-scoring (batched)

**Deviation from original plan (Ollama, MVP):** A documented experiment tested multiple local Ollama models (llama3.2:3b, llama3.1:8b) against Gemini on real, long conversations. Local models reliably followed the required JSON schema on short test inputs but became unreliable — inventing formats, returning empty results, or echoing unrelated prior context — on real, multi-turn conversations. Gemini handled the same real data correctly on the first attempt. Full experiment log preserved in `docs/devmind-mvp-plan.md`.

**Known constraint:** Free tier limited to 20 requests/day per model — a real, hit constraint during development (documented, with batching implemented as a direct mitigation for the job fit-scoring feature specifically).

Status: ✅ Implemented, with real-world reliability data backing the choice

---

## Embedding Model

### Gemini Embeddings (gemini-embedding-001)

**Deviation from original plan (Nomic Embed Text, local):** Adopted to keep a single provider (Gemini) across generation and embeddings, simplifying the integration surface. Uses `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` task types appropriately for stored memories versus search queries.

Status: ✅ Implemented as the sole embedding provider in production

---

## External Job Data Sources

Not present in the original plan — added for the Career Intelligence feature.

### Himalayas (primary, no setup required)
Official, free public API. Remote-jobs focused. Zero authentication, zero cost, no rate-limit issues encountered.

### Apify — Rapid LinkedIn Jobs Scraper (per team direction)
Paid, per-use ($0.50/1,000 results), scrapes LinkedIn's public job search pages (no login required, no personal account risk). Used specifically per explicit team direction, given LinkedIn has no free official job-search API.

**Real constraints hit during development:** monthly credit exhausted on first account during initial testing; field-naming (snake_case, not camelCase) differs from the UI labels and required inspecting the Actor's actual stored input to discover; a minimum `jobs_entries >= 10` validation rule is undocumented in the UI.

Status: ✅ Both sources implemented behind a common, swappable interface (`search_jobs()` returning a normalized shape) — adding or switching sources requires no changes to the worker or scoring logic

---

## Authentication

### API Key (Bearer token)

**Deviation from original plan (JWT):** A single hashed API key per user, checked via a shared `get_current_user` FastAPI dependency across every endpoint and connector. Simpler for the current single-user development stage; JWT remains the natural next step once real multi-user login is needed.

Status: ✅ Implemented across all endpoints and all four connectors

---

## Model Context Protocol (MCP)

Not present in the original plan — added to make DevMind's data queryable directly from AI coding tools in natural conversation.

`mcp_server.py` exposes four tools: `get_developer_profile`, `search_memories`, `get_recommendations`, `get_career_matches` — each a thin wrapper calling DevMind's own REST API.

Status:
- ✅ Claude Desktop — verified working with real data
- ✅ Cursor — verified working with real data
- ✅ Antigravity IDE — verified working with real data
- ⏸️ Codex — correctly configured (standalone CLI, not the VS Code extension, which has a known MCP-detection bug) but blocked by an unrelated account usage limit

---

## Automation

### Windows Task Scheduler

- **Nightly**: runs all four connectors (Claude Code, Codex, Cursor, Antigravity) automatically, capturing new sessions with zero manual steps
- **Weekly**: runs career/job matching separately, deliberately kept apart from the nightly sync to conserve Gemini/Apify quota and credit

Status: ✅ Implemented and verified with real, unattended captures of genuinely new sessions

---

## Deployment

### Docker + Docker Compose

Runs PostgreSQL, Redis, and ChromaDB as isolated, reproducible services.

Status: ✅ Implemented as planned

---

## Version Control

### Git + GitHub

Status: ✅ Implemented as planned

---

# Architecture Summary — As Built

| Layer | Planned | As Built | Status |
|---|---|---|---|
| Frontend | Next.js + React | — | Not started |
| Backend | FastAPI | FastAPI | ✅ |
| Authentication | JWT | API Key (Bearer) | ✅ (deviated, documented reason) |
| Database | PostgreSQL | PostgreSQL | ✅ |
| Vector DB | ChromaDB | ChromaDB | ✅ |
| Cache/Queue | Redis + Celery | Redis + Celery | ✅ |
| Agentic AI | LangGraph | LangGraph | ✅ (learning exercise, 2 working agents) |
| Embeddings | Nomic Embed Text | Gemini Embeddings | ✅ (deviated, documented reason) |
| LLM | Ollama (MVP) | Gemini | ✅ (deviated, documented experiment) |
| Job Data | Not planned | Himalayas + Apify | ✅ (added for Career Intelligence) |
| MCP Integration | Not planned | Claude Desktop, Cursor, Antigravity, Codex | ✅ (3 of 4 verified) |
| Automation | Not planned | Windows Task Scheduler | ✅ |
| Deployment | Docker | Docker + Docker Compose | ✅ |
| Version Control | Git + GitHub | Git + GitHub | ✅ |