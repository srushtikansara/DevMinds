# DevMind — Cross-AI Developer Intelligence Platform
 
DevMind captures a developer's real activity across AI coding tools (Claude Code, Cursor, etc.) and GitHub, builds a persistent memory and skill profile from it, and turns that into career tooling, a grounded learning coach, and safe office automation — all accessible naturally through MCP from any AI client.
 
## Core idea
 
Most AI coding assistants forget everything between sessions. DevMind sits alongside them, ingesting real conversations and commits, extracting concrete events and skill signal, and using that as grounded, factual context for downstream features — instead of generic, one-size-fits-all advice.
 
Every piece of coaching or career content DevMind produces is explicitly traceable back to real events, and the system is built to say "I don't have enough signal for that yet" rather than invent plausible-sounding filler.
 
---
 
## Features
 
### 1. Developer Profile & Skill Tracking
Automatically tracked skills and proficiency scores, built from real activity — not self-reported.
 
### 2. Career Intelligence
- Ranked job matches from real postings, scored by fit
- One-click "Prepare Application": tailored summary + honest gap analysis
- Auto-logs the application to Notion
- Auto-drafts (never sends) a follow-up email in Gmail
### 3. Learning Coach
- Mentorship-style plans grounded in real, linked events (`getting_started` / `next_level` modes)
- `relearn` mode: an honest cross-tool summary of what's actually been covered for a skill, clearly distinguishing guaranteed direct evidence from inferred, adjacent context
- Real, current learning resources (YouTube, articles, documentation) via Tavily web search, cached 24h in Redis
- Backed by real job market demand data for the skill
### 4. Office Automation (general-purpose, via MCP)
- `draft_email` — drafts in Gmail, never sends
- `log_to_notion` — logs a note to a general Notion database
### 5. Saved Workflows
- `workflow_high_fit_job_alert` — a scheduled task that finds new high-fit job matches and batches Notion logging + Gmail drafts automatically
- `generate_weekly_report` — runs automatically after each session; posts a formatted summary (new memories, active skills, open recommendations) to Slack
### 6. Integrations
 
| Service | What it does | Mode |
|---|---|---|
| GitHub | Commit history feeds skill tracking | Read |
| Notion | Job applications + general notes, two databases | Write (log only) |
| Gmail | Follow-up email drafts | Draft only, never sends |
| Google Drive | Resume storage, shareable links | Write |
| Google Calendar | Learning-block scheduling | Write (creates real events) |
| Slack | Weekly summary posts | Write (posts immediately) |
 
**Design principle:** every action that *sends* or *executes* something (email, calendar event, Slack message) is either draft-only or requires the user's own trigger — nothing auto-executes on a third party without a human having set it in motion.
 
---
 
## Architecture
 
```
Session upload (Claude Code / Cursor export)
        |
        v
  parser_worker.py  -->  Conversation + turns stored
        |
        v
  event_extractor_worker.py  -->  DeveloperEvents (with technology_tags)
        |                              |
        v                              v
  skill_worker.py              generate_weekly_report.delay()
  (process_skills)              generate_resume.delay()
        |
        v
  Skill + SkillEvent (traceable link between skill and its real source event)
        |
        v
  Memory pipeline (embeddings -> ChromaDB, dedup/reinforce via similarity threshold)
```
 
**Agents** (LangGraph):
- `career_agent.py` — job research, fit scoring, application prep
- `learning_agent.py` — skill coaching, relearn summaries, web resource search
**Queue:** Celery + Redis — all long-running work (LLM calls, extraction, report generation) runs async.
 
**Vector store:** ChromaDB, for semantic memory search.
 
**MCP server:** `mcp_server.py` — exposes 7 tools (`get_developer_profile`, `search_memories`, `get_recommendations`, `get_career_matches`, `get_learning_coaching`, `draft_email`, `log_to_notion`) to any MCP-compatible AI client (Claude Desktop, etc.).
 
---
 
## Setup
 
### Prerequisites
- Python 3.11+
- Docker + Docker Compose (PostgreSQL, Redis, ChromaDB)
- Node.js (frontend)
### 1. Clone and install
 
```powershell
git clone <repo-url>
cd DevMind/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --break-system-packages
```
 
### 2. Environment variables
 
Create `.env` in `backend/`:
 
```
GEMINI_API_KEY=your-key
GEMINI_API_KEY_TESTING=your-testing-key
TAVILY_API_KEY=your-tavily-key
DEVMIND_API_KEY=your-dev-key
NOTION_TOKEN=your-notion-integration-token
NOTION_DATABASE_ID=your-job-applications-db-id
NOTION_OFFICE_DATABASE_ID=your-office-notes-db-id
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
DATABASE_URL=postgresql://devmind:devmind@localhost:5432/devmind
```
 
### 3. Google OAuth (Gmail, Drive, Calendar)
 
Download `credentials.json` from Google Cloud Console (OAuth client, Desktop app type) into `backend/`. Each service authenticates on first use and stores its own token file (`gmail_token.json`, `drive_token.json`, `calendar_token.json`) — **do not commit these**, they contain real credentials.
 
### 4. Start infrastructure
 
```powershell
docker compose up -d
```
 
### 5. Start the backend
 
```powershell
uvicorn app.main:app --reload
```
 
### 6. Start Celery
 
```powershell
celery -A app.infrastructure.queue.celery_app worker --loglevel=info --pool=solo
```
 
### 7. Start the frontend
 
```powershell
cd frontend
npm install
npm run dev
```
 
### 8. Connect via MCP (Claude Desktop)
 
Add `mcp_server.py` as an MCP server in Claude Desktop's config, pointing to the `backend/` directory. Restart Claude Desktop fully after any change to `mcp_server.py` — tool registration doesn't hot-reload.
 
---
 
## Known limitations & honest notes
 
- **Slack and Calendar have no draft mode** — messages send / events create immediately, unlike Gmail's draft-only approach. Treat these as lower-caution integrations accordingly.
- **SkillEvent backfill is a one-time, manual process** for events processed before a given fix — new events link automatically going forward, but historical events need `process_skills.delay(event_id)` run explicitly if they predate a pipeline change.
- **Web search results cache for 24h** in Redis — a skill's resources won't refresh more often than that even if better results exist.
- **Gemini free-tier quota is a real, ongoing constraint** during active development and testing; consider a paid tier (Vertex AI) if this becomes a persistent blocker.
---
 
## Development notes
 
- Celery workers must be **fully restarted** (not just the code saved) to pick up changes — a stale worker running old code has been the single most common source of "this fix isn't working" confusion during development.
- Always build `skill_names` from raw tags *before* applying any exclusion filter, never after — a missing extraction line here previously caused a silent `NameError` that broke all skill/event linking for hours without any visible error, since it was caught only by a generic retry handler.
- Skill tag normalization (`.lower().replace("_", "-").replace(" ", "-")`) prevents near-duplicate skills (e.g. `deep_learning` vs `deep-learning`) from fragmenting signal across two separate rows.
- When debugging a task that "should have changed but didn't," check for duplicate/stale worker processes before assuming the code itself is wrong.