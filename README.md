# MCP Server Auditor

Audits Model Context Protocol (MCP) servers for safety risks, misleading tool
descriptions, prompt injection vulnerabilities, excessive privilege, and
other reliability/security concerns, producing a structured audit report
with findings, evidence, severity, and an overall risk score.

This repository is being built incrementally, phase by phase. **Phase 0
(project foundation)**, **Phase 1 (MCP server ingestion)**, and **Phase 2
(MCP discovery)** are complete: a runnable FastAPI backend with server
registration and tool-discovery endpoints, a Next.js frontend, and
PostgreSQL/Redis infrastructure via Docker Compose.

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

Apply database migrations:

```powershell
alembic upgrade head
```

This creates the `mcp_servers` table used by the server registration API
(see [API Endpoints](#api-endpoints) below).

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

## API Endpoints

### Health

- `GET /health` - liveness/readiness check.

### MCP Servers (Phase 1)

Register and manage MCP server configurations to be audited. Supported
`source_type` values: `LOCAL_COMMAND`, `HTTP`, `MANUAL_CONFIGURATION`
(`SSE` and `PACKAGE` are modeled but not yet accepted). `connection_config`
is validated against a schema specific to `source_type` and is encrypted at
rest (see `ENCRYPTION_KEY` in `.env.example`) - it is never stored in
plaintext, though it is returned decrypted to API callers since there is no
auth layer yet.

- `POST /servers` - create a server. Body:
  ```json
  {
    "name": "weather-mcp",
    "source_type": "HTTP",
    "connection_config": { "url": "https://example.com/mcp", "headers": {} }
  }
  ```
- `GET /servers` - list servers (supports `skip`/`limit` query params).
- `GET /servers/{id}` - fetch a single server, 404 if not found.
- `DELETE /servers/{id}` - delete a server, 404 if not found.

### MCP Discovery (Phase 2)

Connects to a registered server and discovers its available tools per the
[MCP specification](https://modelcontextprotocol.io/specification/2025-06-18)
(`initialize` -> `initialized` -> `tools/list`, with pagination). Supports
the `stdio` transport (`LOCAL_COMMAND`) and `Streamable HTTP` transport
(`HTTP`); `MANUAL_CONFIGURATION` servers read tools directly from a
`details.tools` array instead of connecting live. Discovered tools are
normalized and persisted, replacing the server's previous tool snapshot.

- `POST /servers/{id}/discover` - run discovery now. Always returns 200; the
  body's `status` field is `SUCCESS` or `FAILED` (e.g. unreachable server),
  with a sanitized `error` message on failure. 404 only if the server
  itself doesn't exist.
- `GET /servers/{id}/tools` - return the most recently discovered tools
  without making a live connection.

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

## Definition of Done (Phase 1)

- [x] `POST/GET /servers`, `GET/DELETE /servers/{id}` implemented and tested.
- [x] `MCPServer` model, Pydantic schemas, repository, and service layer added.
- [x] Config validated per `source_type` (`LOCAL_COMMAND`, `HTTP`,
      `MANUAL_CONFIGURATION`); unsupported types rejected with a 422.
- [x] `connection_config` encrypted at rest via Fernet (`ENCRYPTION_KEY`).
- [x] Hand-written Alembic migration for the `mcp_servers` table (run
      `alembic upgrade head` against a live Postgres to apply it).
- [x] Tests cover create/list/get/delete, validation errors, and the
      encryption round trip.

## Definition of Done (Phase 2)

- [x] `MCPClient` abstraction (`backend/app/mcp/`) isolated from audit logic,
      with `StdioMCPClient`, `HttpMCPClient`, and `ManualMCPClient`.
- [x] Discovery follows the real MCP handshake (`initialize` /
      `notifications/initialized` / `tools/list`, with pagination) - not
      invented protocol behavior.
- [x] Connects safely: per-attempt timeout, sanitized error messages (no
      secrets/env vars/headers logged or returned).
- [x] Discovered tools normalized into `ToolProfile` and persisted
      (`mcp_server_tools` table); `MCPServer` tracks last discovery
      status/timestamp/error.
- [x] `POST /servers/{id}/discover` and `GET /servers/{id}/tools` implemented.
- [x] Tests cover all three clients (real subprocess for stdio, mocked
      transport for HTTP, no I/O for manual) plus the end-to-end API flow,
      including timeout, crash, and unreachable-server failure paths.

## Roadmap

See [PROJECT_PLAN.md](./PROJECT_PLAN.md) for the full phase-by-phase plan
(architecture, domain model, scoring system, coding standards, and Phase
0–9 breakdown with status). Phases are implemented incrementally; later
phases are not started until the current phase is confirmed complete.
