# Sprint 0 — Reproducible engineering foundation

**Dates:** 2026-07-17 to 2026-07-31  
**Capacity:** focused foundation delivery  
**Sprint Goal:** CPMS installs from a pinned CPython 3.12 lockfile, starts with typed config and secret-safe logging, exposes live/ready health against PostgreSQL 18 and RabbitMQ, and passes CI quality gates without OpenStackSDK or Valkey runtime dependencies.

## Selected stories

| Story | Points | Owner | OSPS dependency | Status |
|---|---:|---|---|---|
| CPMS-001 | 5 | Agent | none | Ready |
| CPMS-002 | 5 | Agent | none | Ready |
| CPMS-003 | 3 | Agent | none | Ready |
| CPMS-004 | 5 | Agent | none | Ready |

## Delivery tasks

- [ ] Confirm contract/schema readiness (none required for Sprint 0 domain contracts).
- [ ] Add failing acceptance/unit tests for each story.
- [ ] Implement the smallest vertical slice per story.
- [ ] Add integration coverage for PostgreSQL/RabbitMQ readiness.
- [ ] Verify redaction, observability, and failure behavior.
- [ ] Update operational documentation for local start/health.
- [ ] Run the Definition of Done quality gates.

## Story details

### CPMS-001 — Bootstrap a reproducible Python service

- **Depends on:** none
- **Acceptance:** clean checkout installs from lock; service starts; format/lint/type/unit commands pass; runtime reports Python 3.12; no OpenStackSDK dependency.
- **Verification:** `uv sync --frozen` (or equivalent), `pytest`, `ruff`, `mypy`, `python -c` version check, dependency graph scan.

### CPMS-002 — Typed configuration and secret-safe logging

- **Depends on:** CPMS-001
- **Acceptance:** missing required production config fails fast; password/token/authorization/`user_data` redact in tests; correlation ID accepted or generated and returned.
- **Verification:** unit tests for settings validation, redaction filter, correlation middleware.

### CPMS-003 — Health and local infrastructure integration

- **Depends on:** CPMS-001
- **Acceptance:** liveness is process-only; readiness false when DB or RabbitMQ unavailable; Valkey is not a readiness dependency.
- **Verification:** unit tests with fakes; integration tests against Compose PostgreSQL/RabbitMQ.

### CPMS-004 — CI quality pipeline

- **Depends on:** CPMS-001..003
- **Acceptance:** CI runs lock verification, formatting, lint, typing, unit tests, integration tests with PostgreSQL/RabbitMQ, migration check, contract validation, and secret scan.
- **Verification:** GitHub Actions (or equivalent) workflow dry-run locally via the same commands.

## Risks and impediments

| Risk/impediment | Owner | Mitigation | Status |
|---|---|---|---|
| Local Python alias points to Store stub | Agent | Use `py -3.12` / explicit 3.12 interpreter | Mitigated |
| Sprint 1 migrations/contracts not present yet | Agent | Provide empty-safe migration/contract CI checks without domain scaffold | Open |
| Compose services must remain running | Agent | Do not recreate volumes; use existing healthy stack | Open |

## Review evidence

- Demo scenario: start CPMS API, call `/health/live` and `/health/ready` against local Compose.
- Test/migration commands and results: _(filled at story completion)_
- Contract checksum: N/A (no domain contracts in Sprint 0)
- Known limitations: no provider/domain APIs; Alembic has empty baseline only for CI migration check; Valkey present in Compose but unused by CPMS.

## Retrospective actions

- Keep: _(filled at sprint end)_
- Improve: _(filled at sprint end)_
- One measurable action for next sprint: _(filled at sprint end)_
