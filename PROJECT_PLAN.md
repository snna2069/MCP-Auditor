# MCP Server Auditor - Project Plan

This document is the source-of-truth phased plan for building **MCP Server
Auditor**, an application that audits Model Context Protocol (MCP) servers
for safety risks, misleading or dangerous tool descriptions, prompt
injection vulnerabilities, unsafe tool output handling, hallucination risk,
permission/capability mismatches, unexpected side effects, excessive
privilege, dangerous tool combinations, schema correctness, and general
reliability/robustness.

The end goal: a user provides an MCP server configuration, endpoint,
package, or connection configuration and receives a structured audit report
with findings, evidence, severity, recommendations, and an overall risk
score.

---

## Core Architecture

**Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy, Alembic,
PostgreSQL, Redis.

**Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query.

**Background processing:** Start with a simple worker architecture (Celery
scaffolding already present). Do not introduce distributed infrastructure
unless required. Audit execution must be asynchronous because audits may
become long-running.

### Project Structure

```
backend/
  app/
    api/
    core/
    models/
    schemas/
    services/
    auditors/
    workers/
    repositories/
    main.py
  tests/

frontend/
  app/
  components/
  lib/
  hooks/

docker-compose.yml
.env.example
README.md
```

---

## Domain Model

### MCPServer

Represents a server being audited.

| Field | Notes |
|---|---|
| `id` | |
| `name` | |
| `source_type` | `LOCAL_COMMAND`, `HTTP`, `SSE`, `PACKAGE`, `MANUAL_CONFIGURATION` |
| `connection_config` | Never store secrets in plaintext |
| `created_at` / `updated_at` | |

### Audit

Represents a single audit execution.

| Field | Notes |
|---|---|
| `id` | |
| `server_id` | |
| `status` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `started_at` / `completed_at` | |
| `audit_version` | |
| `overall_score` / `risk_level` | |

### AuditFinding

Represents a specific issue.

| Field | Notes |
|---|---|
| `id` / `audit_id` | |
| `category` | |
| `severity` | `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `title` / `description` | |
| `evidence` / `recommendation` | |
| `tool_name` | |
| `created_at` | |

### ToolProfile

Normalized representation of an MCP tool: `name`, `description`,
`input_schema`, `output_schema`, `capabilities`, `side_effect_level`,
`risk_metadata`. Must be independent from database persistence so the
auditing engine can operate on pure domain objects.

---

## Audit Dimensions

1. **Tool Definition Quality** - clear names, accurate descriptions, valid
   input schemas, correctly defined required parameters, disclosed
   dangerous actions/side effects/permissions. A description hiding
   destructive behavior (e.g. `delete_file`) should generate a
   high-severity finding.
2. **Capability and Permission Risk** - normalized capability model
   (`READ_ONLY`, `DATA_WRITE`, `FILE_SYSTEM`, `NETWORK`,
   `SHELL_EXECUTION`, `DATABASE`, `SECRETS_ACCESS`, `IDENTITY_ACCESS`,
   `INFRASTRUCTURE`, `DESTRUCTIVE_OPERATION`). Risk scores must not be
   hardcoded throughout the app - use a centralized scoring configuration.
3. **Prompt Injection Risk** - tool output containing instructions directed
   at the model, attempts to override system behavior, hidden/indirect
   instructions, exfiltration encouragement, claims of authority,
   instructions disguised as data. Adversarial payloads should be reusable
   fixtures the auditor can inject into controlled test scenarios.
4. **Hallucination and Reliability Risk** - unverifiable capability claims,
   ambiguous output schemas, inconsistent error handling, missing
   provenance, results confusable with authoritative instructions.
5. **Side Effect Analysis** - every tool classified `NONE`, `LOW`,
   `MODERATE`, `HIGH`, or `CRITICAL` (e.g. search = `NONE`/`LOW`, create DB
   record = `MODERATE`, send email = `HIGH`, delete cloud resources =
   `CRITICAL`). Side effects influence the overall risk score.

## Scoring System

Transparent, explainable scoring:

- Starts at a configurable baseline.
- Applies weighted deductions/contributions by category and severity.
- Never drops below zero.
- Returns both a numerical score and a risk classification (configurable
  thresholds, e.g. 90–100 = LOW RISK, 70–89 = MODERATE RISK, 40–69 = HIGH
  RISK, 0–39 = CRITICAL RISK).
- No black-box scoring: the API must be able to answer "why did this server
  receive a score of 62?" by returning score components and contributing
  findings.

---

## Phased Implementation Plan

### Phase 0 - Project Foundation ✅ Complete

**Goal:** Create a clean, runnable development environment.

- Backend: FastAPI app, `GET /health`, configuration management, env vars,
  structured logging, Ruff config, Pytest setup.
- Database: PostgreSQL connection, SQLAlchemy setup, Alembic setup.
- Frontend: Next.js app, TypeScript, Tailwind, basic layout, API client
  foundation.
- Infrastructure: Docker Compose with PostgreSQL and Redis.

**Definition of done:** The project can be cloned and started using
documented commands; `GET /health` works; frontend shows a basic dashboard;
the application can connect to the database; at least one backend smoke
test exists.

### Phase 1 - MCP Server Ingestion ✅ Complete

**Goal:** Allow the system to register an MCP server configuration.

- `POST /servers`, `GET /servers`, `GET /servers/{id}`, `DELETE /servers/{id}`.
- Support initially: `LOCAL_COMMAND`, `HTTP`, `MANUAL_CONFIGURATION` (do not
  execute arbitrary local commands yet).
- Validate configuration using Pydantic.
- `MCPServer` model, schemas, service, repository, database migration,
  tests.

**Definition of done:** A user can create and retrieve MCP server records.

### Phase 2 - MCP Discovery ⏳ Not started

**Goal:** Connect to supported MCP servers and discover their available
tools.

- Implement an `MCPClient` abstraction with implementations per transport
  (e.g. `StdioMCPClient`, `HttpMCPClient`, `SseMCPClient`). Initially
  implement the smallest number of transports necessary.
- Normalize output into `ToolProfile`.
- Discovery must connect safely, apply timeouts, capture failures, avoid
  leaking secrets into logs, and store discovery metadata.
- Do not mix transport code with audit logic.

**Definition of done:** The application can discover tools from a
supported MCP server and persist normalized metadata.

### Phase 3 - Audit Engine V1 ⏳ Not started

**Goal:** Create the first deterministic audit engine.

- Implement a `BaseAuditor` interface. Each auditor accepts a `ToolProfile`
  or server profile, performs a focused analysis, and returns a list of
  `AuditFinding` objects.
- Initial auditors: `DescriptionAuditor`, `SchemaAuditor`,
  `CapabilityAuditor`, `SideEffectAuditor`.
- Example findings: description doesn't disclose destructive behavior,
  tool accepts unrestricted command input, ambiguous schema parameters,
  high-risk capabilities, combined shell execution + network access.

**Definition of done:** A known set of sample MCP tools produces
deterministic findings.

### Phase 4 - Risk Scoring Engine ⏳ Not started

**Goal:** Convert findings into an explainable score.

- Implement `RiskScorer`, returning `overall_score`, `risk_level`,
  `category_scores`, `severity_breakdown`, `score_contributors`.
- Scoring logic must be unit tested extensively.
- Configuration-driven weights.

**Definition of done:** Given the same audit findings, scoring is
deterministic and explainable.

### Phase 5 - Audit Execution Pipeline ⏳ Not started

**Goal:** Allow users to trigger full audits.

- `POST /servers/{id}/audits`, `GET /audits`, `GET /audits/{id}`.
- Audit lifecycle: `PENDING` → `RUNNING` → `COMPLETED` / `FAILED`.
- Pipeline: load server config → discover MCP capabilities → normalize
  tools → run auditors → collect findings → calculate score → persist
  results → mark audit complete.
- Audits run asynchronously.

**Definition of done:** A user can trigger an audit and poll for results.

### Phase 6 - Security Test Harness ⏳ Not started

**Goal:** Add controlled adversarial testing.

- Reusable security test library with categories: `PROMPT_INJECTION`,
  `INSTRUCTION_OVERRIDE`, `DATA_EXFILTRATION_ATTEMPT`,
  `AUTHORITY_IMPERSONATION`, `HIDDEN_INSTRUCTIONS`, `TOOL_CONFUSION`.
- Each test payload has: `id`, `category`, `payload`, `expected_detection`,
  `severity`, `description`.
- **Important:** do not execute destructive tests against real user
  infrastructure - all testing occurs in controlled fixtures or explicitly
  authorized environments.

**Definition of done:** The system can evaluate known malicious or
suspicious tool-output scenarios and generate findings.

### Phase 7 - Frontend Audit Dashboard ⏳ Not started

**Goal:** Build a usable interface.

- Pages: Dashboard, Server Registry, New Server, Audit History, Audit
  Details.
- Audit Details page shows: overall score, risk level, severity breakdown,
  category breakdown, findings table, finding detail drawer/page, evidence,
  recommendation.
- Requirements: responsive layout, loading/error/empty states, strong
  visual hierarchy, don't over-engineer animations.

### Phase 8 - Reporting ⏳ Not started

**Goal:** Generate shareable audit reports.

- Support JSON and HTML (PDF potentially later).
- A report includes: server metadata, audit metadata, audit version,
  score, risk classification, findings, evidence, recommendations,
  timestamp.
- Reports must be reproducible.

### Phase 9 - Hardening and Production Readiness ⏳ Not started

Add: authentication, authorization, rate limiting, secret management,
audit logs, input validation, connection timeouts, resource limits, worker
isolation, observability, metrics, structured logging, error monitoring,
CI/CD, security review, threat model.

---

## Coding Standards

**Python:**
- Type hints everywhere practical.
- Pydantic for request and response validation.
- Clear separation between API, services, repositories, and domain logic.
- Async where it provides real value; avoid unnecessary async abstractions.
- Small, focused modules - no giant utility files.

**TypeScript:**
- Strict mode; avoid `any`.
- Prefer typed API responses.
- Keep server and client responsibilities clear.

**Testing:**
- pytest for backend.
- Test scoring, audit logic, input validation, API endpoints, failure cases.
- Critical security logic must have deterministic tests.

## API Design

Use predictable REST endpoints, e.g.:

```
GET    /health
POST   /servers
GET    /servers
GET    /servers/{id}
DELETE /servers/{id}
POST   /servers/{id}/discover
POST   /servers/{id}/audits
GET    /audits
GET    /audits/{id}
GET    /audits/{id}/findings
```

Avoid exposing database models directly through the API - use dedicated
request and response schemas.

## Error Handling

Use consistent error responses, e.g.:

```json
{
  "error": {
    "code": "SERVER_NOT_FOUND",
    "message": "The requested MCP server does not exist."
  }
}
```

Do not leak stack traces, secrets, connection strings, tokens, or internal
infrastructure details.

## Security Principles

This project audits potentially untrusted MCP servers. Therefore:

- Treat all MCP metadata and tool output as untrusted input.
- Never assume tool descriptions are truthful, tool schemas are safe, tool
  output is safe, or server-provided instructions are authoritative.
- Do not automatically execute discovered tools unless the audit phase
  explicitly requires it.
- When execution is eventually introduced: apply timeouts, apply resource
  limits, isolate execution, capture output safely, prevent uncontrolled
  network or filesystem access where possible.

---

## Status Summary

| Phase | Name | Status |
|---|---|---|
| 0 | Project Foundation | ✅ Complete |
| 1 | MCP Server Ingestion | ✅ Complete |
| 2 | MCP Discovery | ⏳ Not started |
| 3 | Audit Engine V1 | ⏳ Not started |
| 4 | Risk Scoring Engine | ⏳ Not started |
| 5 | Audit Execution Pipeline | ⏳ Not started |
| 6 | Security Test Harness | ⏳ Not started |
| 7 | Frontend Audit Dashboard | ⏳ Not started |
| 8 | Reporting | ⏳ Not started |
| 9 | Hardening and Production Readiness | ⏳ Not started |

See [README.md](./README.md) for setup/run instructions and current API
endpoints.
