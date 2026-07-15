# DevMind - Cross-AI Developer Intelligence Platform

> A production-ready platform that transforms AI-assisted developer interactions into persistent knowledge, developer intelligence, and personalized learning insights.

---

## Overview

Modern developers use multiple AI tools such as Claude Code, ChatGPT, Cursor, GitHub Copilot, VS Code, Terminal, and documentation websites throughout their development workflow. However, these interactions remain fragmented, resulting in lost context, repeated questions, and no long-term understanding of a developer's growth.

The **Cross-AI Developer Intelligence Platform** aims to solve this problem by capturing AI sessions, building long-term developer memory, tracking technical skills, and generating actionable insights to support continuous learning and career development.

---

## Problem Statement

Current AI tools provide excellent assistance during individual sessions but lack:

- Persistent developer memory
- Cross-platform AI intelligence
- Long-term learning analytics
- Unified developer profile
- Personalized career recommendations

This platform bridges that gap by creating a centralized intelligence layer across AI-assisted development workflows.

---

## MVP Features

- Claude Code, Codex, and Cursor integration
- AI session ingestion
- Session processing pipeline
- Long-term memory engine
- Semantic search
- Developer profile generation
- Weekly developer reports
- Learning recommendations

---

## Future Features

- ChatGPT Integration
- GitHub Integration
- VS Code Extension
- Terminal Integration
- Browser Extension
- Knowledge Graph
- Multi-Agent Workflows
- Team Analytics
- Resume Tailoring
- Job & Company Recommendations
- Human-in-the-Loop (HITL) job application workflow

---

## System Architecture

```text
AI Platform
      │
      ▼
Connector Layer
      │
      ▼
Session Ingestion
      │
      ▼
Processing Pipeline
      │
      ▼
Memory Engine
      │
      ├────────► PostgreSQL
      │
      └────────► ChromaDB
      │
      ▼
Developer Profile
      │
      ▼
Recommendation Engine
      │
      ▼
Report Generation
      │
      ▼
Dashboard / API
```

---

## Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | Next.js + React |
| Backend | FastAPI |
| Authentication | JWT |
| Database | PostgreSQL |
| Vector Database | ChromaDB |
| Cache | Redis |
| Background Jobs | Celery |
| Workflow Engine | LangGraph |
| Embeddings | Nomic Embed Text |
| LLM | Ollama (MVP) |
| Monitoring | Prometheus + Grafana |
| Logging | Loguru |
| Containerization | Docker |
| CI/CD | GitHub Actions |

---

## Project Structure

```text
backend/
├── app/
│   ├── config.py                 # Settings loaded from .env
│   ├── domain/                   # Business entities (framework-agnostic)
│   ├── infrastructure/
│   │   ├── db/                    # SQLAlchemy models, session, Base
│   │   ├── queue/                 # Celery app configuration
│   │   ├── llm/                   # LLM provider adapters (planned)
│   │   ├── embeddings/            # Embedding provider adapters (planned)
│   │   └── vectorstore/           # ChromaDB client wrapper (planned)
│   └── interfaces/http/           # FastAPI routers (POST /sessions, etc.)
├── workers/                       # Celery tasks (parser, event extraction, etc.)
├── alembic/                       # Database migrations
└── requirements.txt

connectors/                        # Claude Code / Codex / Cursor connector clients (in progress)

docs/
├── devmind-mvp-plan.md            # MVP scope, data models, API contracts, build order
├── Project_vision.md
├── Problem_Statement.md
├── Target_Users.md
├── Existing_Solutions.md
├── MVP.md
├── System_Architecture.md
├── User_Flow.md
├── Component_Design.md
├── Database_Design.md
├── API_Design.md
├── Processing_Pipeline.md
├── Memory_Engine.md
├── Report_Generation.md
├── Concurrency_and_Scalability.md
├── Technology_Stack.md
└── Future_Roadmap.md

docker-compose.yml                 # Postgres, Redis, ChromaDB, backend, celery-worker
```

---

## Development Roadmap

### Phase 1 – MVP

- Claude Code, Codex, and Cursor connectors
- Session processing
- Memory engine
- Developer profile
- Report generation

### Phase 2

- ChatGPT Integration
- GitHub Integration
- VS Code Integration
- Semantic search improvements

### Phase 3

- Learning Intelligence
- Career Intelligence
- Resume Tailoring
- Company Recommendations
- Interview Preparation
- HITL Job Application Workflow

### Phase 4

- Multi-Agent Architecture
- Knowledge Graph
- Team Analytics
- Enterprise Features

---

## Production Design Principles

- Modular Architecture
- Event-Driven Processing
- Asynchronous Workflows
- Background Workers
- Horizontal Scalability
- Stateless Services
- Fault Tolerance
- Clean Architecture
- Domain-Driven Design (DDD)

---

## Goals

- Unify developer interactions across AI tools.
- Build persistent developer memory.
- Track technical growth over time.
- Generate meaningful developer reports.
- Recommend personalized learning paths.
- Support career development through AI-driven insights.

---

## Status

🚧 **Current Stage:** Core Backend Implementation

The full database schema (12 core tables: User, Connector, Session, Conversation,
DeveloperEvent, Memory, Embedding, SkillSignal, Skill, DeveloperProfile,
Recommendation, WeeklyReport) is implemented and migrated. The session-upload
API (`POST /sessions`) is live with verified idempotency, and the background
processing pipeline (Celery + Redis) successfully parses uploaded sessions into
structured conversation data — verified end to end with test data.

**In progress:** building the real Claude Code / Codex / Cursor connector
clients to ingest actual session data, replacing the test payloads used to
validate the pipeline so far.

See [`docs/devmind-mvp-plan.md`](docs/devmind-mvp-plan.md) for the full MVP
scope, data model reference, API contracts, and build order.

---

## Running Locally

```bash
cp .env.example .env      # fill in real values
docker compose up -d postgres redis
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

---

## License

This project is intended for educational, research, and portfolio purposes. The architecture is designed with production-ready principles and can be extended into a scalable SaaS platform.