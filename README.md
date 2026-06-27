# Rubi

Open-source AI Voice Employee for Indian Businesses.

This repository is an MVP scaffold for Rubi: a modular, self-hostable AI voice-agent platform with a FastAPI backend, a Next.js dashboard, provider interfaces, event-driven contracts, and Docker-first local infrastructure.

## What Is Included

- FastAPI backend with typed settings, health checks, auth stub, agent CRUD, call history, knowledge upload metadata, and realtime event stream endpoint.
- Next.js dashboard shell for dashboard, calls, live calls, analytics, knowledge base, tools, settings, users, voices, models, and logs.
- Provider-agnostic interfaces for LLM, STT, TTS, telephony, memory, knowledge search, tools, and agents.
- Twilio inbound call flow that records calls, gathers speech, collects name/need/budget, marks agreement state, and stores readable call notes locally.
- Docker Compose for backend, frontend, PostgreSQL, Redis, Qdrant, MinIO, Ollama, and LiveKit.
- Documentation for architecture, API surface, milestones, and environment setup.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Backend: http://localhost:8000/docs

Frontend: http://localhost:3000

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Vercel Frontend Deployment

Deploy the dashboard from the `frontend` directory on Vercel and set:

```text
NEXT_PUBLIC_API_URL=https://your-live-backend-domain.com
```

See `docs/VERCEL_DEPLOYMENT.md` for the full safe deploy checklist.

## MVP Scope

Phase 1 focuses on Twilio phone intake, recording callbacks, readable call summaries, website-knowledge answers, and dashboard workflows. Add real website content to `docs/business_knowledge.md`.
