# MCP Server Auditor

Audits Model Context Protocol (MCP) servers for safety risks, misleading tool
descriptions, prompt injection vulnerabilities, excessive privilege, and
other reliability/security concerns, producing a structured audit report
with findings, evidence, severity, and an overall risk score.

This repository is being built incrementally, phase by phase. **Phase 0
(project foundation)** is complete: a runnable FastAPI backend, a Next.js
frontend, and PostgreSQL/Redis infrastructure via Docker Compose.

## Project Structure

```
backend/    FastAPI + SQLAlchemy + Alembic application
frontend/   Next.js + TypeScript + Tailwind + TanStack Query application
docker-compose.yml   PostgreSQL + Redis for local development
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop (with WSL2 or Hyper-V backend enabled on Windows)

## 1. Configure environment variables

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env.local
```

The defaults match `docker-compose.yml` and work out of the box for local
development.

## 2. Start infrastructure (PostgreSQL + Redis)

```powershell
docker compose up -d
```

This starts:
- PostgreSQL on `localhost:5432` (db `mcp_auditor`, user/password `mcp`/`mcp`)
- Redis on `localhost:6379`

Verify both containers are healthy:

```powershell
docker compose ps
```

## 3. Start the backend (FastAPI)

```powershell
cd backend
python -m venv .venv          # first time only
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # first time only / after dependency changes

uvicorn app.main:app --reload --port 8000
```

The backend is now available at http://localhost:8000. Verify it's running:

```powershell
curl http://localhost:8000/health
```

Apply database migrations (once models exist, starting in Phase 1):

```powershell
alembic upgrade head
```

### Run backend tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

### Run backend formatting/linting

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
ruff format .
ruff check . --fix
```

## 4. Start the frontend (Next.js)

```powershell
cd frontend
npm install   # first time only / after dependency changes
npm run dev
```

The frontend is now available at http://localhost:3000 and displays a
dashboard with a live backend connectivity check.

### Run frontend lint

```powershell
cd frontend
npm run lint
```

## Definition of Done (Phase 0)

- [x] `GET /health` responds with app status/version/environment.
- [x] Configuration is centralized (`backend/app/core/config.py`) and driven
      by environment variables (root `.env`).
- [x] Structured (JSON) logging configured for the backend.
- [x] Ruff configured for formatting and linting; Pytest configured with a
      smoke test for `/health`.
- [x] SQLAlchemy engine/session and Alembic wired to the same
      `DATABASE_URL` setting (no live DB required to start the API).
- [x] Next.js app with TypeScript, Tailwind, shadcn/ui, and a TanStack Query
      client hitting the backend `/health` endpoint from a basic dashboard.
- [x] `docker-compose.yml` provisions PostgreSQL and Redis for local dev.
- [x] Project can be cloned and started using the commands documented above.

## Roadmap

See the phased implementation plan (Phase 1: MCP server ingestion, Phase 2+:
auditing engine, scoring, etc.) for what's next. Phases are implemented
incrementally; later phases are not started until the current phase is
confirmed complete.
