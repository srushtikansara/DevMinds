# 17_Technology_Stack.md

# Technology Stack

## Backend

### FastAPI

Purpose

- REST APIs
- High Performance
- Async Support

Why?

- Excellent performance
- Native asyncio
- Automatic Swagger Documentation
- Production Ready

---

## Frontend

### Next.js + React

Purpose

- Dashboard
- Developer Profile
- Reports

Why?

- Server Side Rendering
- Modern UI
- Excellent Developer Experience

---

## Database

### PostgreSQL

Purpose

Store structured data

Stores

- Users
- Projects
- Sessions
- Reports
- Skills
- Recommendations

Why?

- ACID Compliance
- Reliable
- Production Ready

---

## Vector Database

### ChromaDB

Purpose

Semantic Search

Stores

- Embeddings
- Memories

Why?

- Lightweight
- Open Source
- Easy Integration

Future

- Pinecone
- Qdrant
- Milvus

---

## Cache

### Redis

Purpose

- Queue
- Cache
- Session Store

Why?

- Fast
- Reliable
- Supports Pub/Sub

---

## Background Processing

### Celery

Purpose

- Report Generation
- Memory Processing
- Event Extraction

Why?

- Retry Support
- Distributed Workers
- Production Ready

Future

- Temporal
- Trigger.dev
- Kafka Consumers

---

## AI Framework

### LangGraph

Purpose

Workflow Orchestration

Why?

- Multi-step AI pipelines
- Stateful execution
- Agent workflows

---

## LLM

MVP

- Ollama (Local)

Future

- OpenAI
- Claude
- Gemini

---

## Embedding Model

### Nomic Embed Text

Purpose

Semantic Search

Why?

- High Quality Embeddings
- Local Inference
- Open Source

---

## Object Storage

Future

- AWS S3
- Azure Blob Storage

Purpose

- Session Files
- Reports
- Attachments

---

## Monitoring

- Prometheus
- Grafana
- OpenTelemetry

---

## Logging

- Loguru
- Structured JSON Logs

---

## Deployment

- Docker
- Docker Compose

Future

- Kubernetes
- Helm
- Terraform

---

## Version Control

- Git
- GitHub

---

# Architecture Summary

| Layer | Technology |
|---------|------------|
| Frontend | Next.js + React |
| Backend | FastAPI |
| Authentication | JWT |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| Cache | Redis |
| Queue | Redis + Celery |
| Memory | LangGraph + ChromaDB |
| Embeddings | Nomic Embed Text |
| LLM | Ollama (MVP) |
| Monitoring | Prometheus + Grafana |
| Logging | Loguru |
| Deployment | Docker |
| Version Control | GitHub |