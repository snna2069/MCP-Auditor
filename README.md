# MCP Server Auditor

Audits Model Context Protocol (MCP) servers for safety risks, misleading tool
descriptions, prompt injection vulnerabilities, excessive privilege, and
other reliability/security concerns, producing a structured audit report
with findings, evidence, severity, and an overall risk score.

This repository is being built incrementally, phase by phase. **Phase 0
(project foundation)**, **Phase 1 (MCP server ingestion)**, **Phase 2 (MCP
discovery)**, **Phase 3 (audit engine v1)**, **Phase 4 (risk scoring
engine)**, **Phase 5 (audit execution pipeline)**, and **Phase 6 (security
test harness)** are complete: a runnable FastAPI backend with server
registration, tool-discovery, and asynchronous full-audit endpoints, a
Next.js frontend, and PostgreSQL/Redis infrastructure via Docker Compose.

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

### Start the audit worker (Celery)

Triggering an audit (`POST /servers/{id}/audits`) enqueues a background job;
a separate worker process executes it asynchronously (requires Redis from
step 2 above):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A app.workers.celery_app worker --loglevel=info
```

Without a running worker, audits will stay `PENDING` forever - `GET
/audits/{id}` lets you poll for status. (Tests run Celery in "eager" mode
in-process, so they don't need a real worker or Redis; see
`backend/tests/conftest.py`.)

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

### Audit Engine (Phase 3)

`backend/app/auditors/` is a deterministic, internal analysis library (no
new API endpoints yet - triggering/persisting full audits is Phase 5). Each
auditor accepts a `ToolProfile` and returns a list of `AuditFinding`s
(`category`, `severity`, `title`, `description`, `evidence`,
`recommendation`). Given the same tool, results are always identical (pure
keyword heuristics, no ML/network calls), so audits are reproducible.

- `DescriptionAuditor` - flags missing/too-brief descriptions and tool
  names/annotations that suggest destructive behavior the description
  doesn't disclose.
- `SchemaAuditor` - flags malformed input schemas, ambiguous (untyped or
  undocumented) parameters, and required parameters missing from
  `properties`.
- `CapabilityAuditor` - infers capability tags (`SHELL_EXECUTION`,
  `NETWORK`, `DATABASE`, `DESTRUCTIVE_OPERATION`, etc.) from tool
  name/description/schema; flags unrestricted command input, dangerous
  capability combinations, and annotation-vs-behavior mismatches.
- `SideEffectAuditor` - classifies each tool `NONE`/`LOW`/`MODERATE`/`HIGH`/
  `CRITICAL` based on inferred capabilities.

`app.auditors.registry.run_auditors(tool)` runs all four against a
`ToolProfile` and returns the combined findings.

### Risk Scoring Engine (Phase 4)

`backend/app/scoring/` converts a list of `AuditFinding`s into an
explainable score via `RiskScorer.score(findings)`. Every number that
influences a score lives in one place, `app.scoring.config.ScoringConfig`
(baseline, per-severity weights, per-category weights, risk-level
thresholds) - nothing is hardcoded in the auditors or elsewhere. The result
(`ScoreResult`) includes:

- `overall_score` - starts at the configurable baseline (100) and is only
  ever reduced by findings, clamped to a minimum of 0.
- `risk_level` - `LOW`/`MODERATE`/`HIGH`/`CRITICAL`, from configurable
  score thresholds.
- `category_scores` - the same baseline-minus-deductions scoring applied
  independently per audit dimension (each category is its own lens, not a
  partition of one shared budget).
- `severity_breakdown` - finding counts per severity.
- `score_contributors` - one entry per finding (tool, category, severity,
  weights, exact point contribution), sorted by impact, so the API can
  eventually answer "why did this server receive a score of 62?".

Given the same findings and config, scoring is always identical (no
randomness) - proven by dedicated determinism tests, including an
end-to-end auditors -> scorer pipeline test.

### Audit Execution Pipeline (Phase 5)

Ties the previous phases together into a triggerable, asynchronous audit.
`POST /servers/{id}/audits` creates an `Audit` row (`PENDING`) and enqueues
a Celery task, returning immediately; a separate worker process runs the
pipeline: load server -> discover MCP capabilities (Phase 2, fresh every
time) -> normalize tools -> run auditors (Phase 3) -> score (Phase 4) ->
persist `AuditFinding` rows -> mark `COMPLETED` (or `FAILED` with a
sanitized `error_message`, never a raw stack trace or secret).

- `POST /servers/{id}/audits` - trigger an audit. Returns 202 with the
  `Audit` in its current state (`PENDING` in real async use; may already
  be `COMPLETED`/`FAILED` if a worker processed it immediately). 404 if the
  server doesn't exist.
- `GET /audits` - list audits (`skip`/`limit`, optional `server_id` filter).
- `GET /audits/{id}` - poll a single audit's status/score/risk_level.
- `GET /audits/{id}/findings` - list the findings persisted for an audit.

Audit lifecycle: `PENDING` -> `RUNNING` -> `COMPLETED` / `FAILED`. The
pipeline never lets an exception escape the worker task - failures are
always recorded on the `Audit` row instead of crashing it.

### Security Test Harness (Phase 6)

`backend/app/security/` is a reusable adversarial-content library, kept
separate from the auditors above since it inspects tool *output* (untrusted
content a tool might return), not tool metadata. Per the project's security
principles, nothing here executes a real MCP tool - it only scans text
handed to it (curated fixtures today; a future, explicitly-authorized
invocation step could feed it real tool-call output).

- `SecurityTestPayload` fixtures (`id`, `category`, `payload`,
  `expected_detection`, `severity`, `description`) cover all six categories
  - `PROMPT_INJECTION`, `INSTRUCTION_OVERRIDE`,
  `DATA_EXFILTRATION_ATTEMPT`, `AUTHORITY_IMPERSONATION`,
  `HIDDEN_INSTRUCTIONS`, `TOOL_CONFUSION` - plus benign "negative control"
  payloads proving the detector doesn't flag ordinary tool output.
- `PromptInjectionDetector.scan(text, tool_name=...)` deterministically
  matches text against per-category regex heuristics and returns
  `AuditFinding`s under `AuditCategory.PROMPT_INJECTION_RISK`, already
  compatible with the existing scoring/persistence layers if wired into a
  live pipeline later.

Tests prove every malicious fixture is detected and every benign one is not.

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

## Definition of Done (Phase 3)

- [x] `BaseAuditor` interface (`backend/app/auditors/`); each auditor takes a
      `ToolProfile` and returns `AuditFinding`s.
- [x] `DescriptionAuditor`, `SchemaAuditor`, `CapabilityAuditor`, and
      `SideEffectAuditor` implemented per the plan.
- [x] Deterministic, keyword-based capability/side-effect inference (no
      ML/network calls) - documented as best-effort signal, not ground truth.
- [x] Findings match the plan's literal examples: destructive tool names
      without disclosure (HIGH), unrestricted command input (CRITICAL),
      shell+network combination (CRITICAL), send email (HIGH), create DB
      record (MODERATE), delete cloud resources (CRITICAL).
- [x] A known set of sample MCP tools produces identical findings across
      repeated runs (determinism test).

## Definition of Done (Phase 4)

- [x] `RiskScorer` (`backend/app/scoring/`) returns `overall_score`,
      `risk_level`, `category_scores`, `severity_breakdown`, and
      `score_contributors`.
- [x] Starts at a configurable baseline, applies weighted deductions by
      severity and category, and never drops below zero.
- [x] All weights/thresholds centralized in `ScoringConfig` - none
      hardcoded in auditors or services; configs are swappable per call.
- [x] No black-box scoring: `score_contributors` explains exactly how much
      each finding contributed.
- [x] Given the same findings, scoring is deterministic (unit tests plus an
      end-to-end auditors -> scorer pipeline test on sample tools).

## Definition of Done (Phase 5)

- [x] `POST /servers/{id}/audits`, `GET /audits`, `GET /audits/{id}`,
      `GET /audits/{id}/findings` implemented.
- [x] Audit lifecycle `PENDING` -> `RUNNING` -> `COMPLETED`/`FAILED`
      persisted on a new `Audit` table; findings persisted on a new
      `AuditFinding` table (hand-written migration).
- [x] Full pipeline wired: fresh discovery -> normalize -> run all 4
      auditors -> score -> persist -> mark complete.
- [x] Runs asynchronously via Celery (`app/workers/`); the worker never lets
      an exception escape (failures recorded as `FAILED` + sanitized
      `error_message`, verified by a dedicated unit test that a raised
      exception's message never leaks into the persisted error).
- [x] Tests cover success (with and without findings), discovery failure,
      missing server, listing/filtering, and 404s for missing
      audits/findings - using Celery's eager mode so no live broker is
      required to test the pipeline deterministically.

## Definition of Done (Phase 6)

- [x] Reusable adversarial payload library (`backend/app/security/`)
      covering all six categories: `PROMPT_INJECTION`,
      `INSTRUCTION_OVERRIDE`, `DATA_EXFILTRATION_ATTEMPT`,
      `AUTHORITY_IMPERSONATION`, `HIDDEN_INSTRUCTIONS`, `TOOL_CONFUSION`.
- [x] Each payload has `id`, `category`, `payload`, `expected_detection`,
      `severity`, `description`, per the plan.
- [x] `PromptInjectionDetector` deterministically evaluates text and
      generates `AuditFinding`s - no real tool is ever executed; testing
      uses controlled fixtures only, per the project's security principles.
- [x] Tests prove every malicious fixture is detected and every benign
      ("negative control") fixture is not, satisfying "the system can
      evaluate known malicious or suspicious tool-output scenarios and
      generate findings."

## Roadmap

See [PROJECT_PLAN.md](./PROJECT_PLAN.md) for the full phase-by-phase plan
(architecture, domain model, scoring system, coding standards, and Phase
0–9 breakdown with status). Phases are implemented incrementally; later
phases are not started until the current phase is confirmed complete.
