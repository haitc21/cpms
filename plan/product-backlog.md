# CPMS Product Backlog

Priorities use Must/Should/Could. Sprint allocation is the initial forecast and may change during refinement without changing dependencies or acceptance criteria.

## Epic CPMS-E0 — Engineering foundation

### CPMS-001 — Bootstrap a reproducible Python service

- **Sprint/Priority/Points:** 0 / Must / 5
- **Depends on:** none
- **Outcome:** developers and CI run the same CPython 3.12 dependency graph.
- **Tasks:** create `pyproject.toml`, src layout, lockfile, application factory, CLI/entrypoint, formatting/lint/type/test configuration, and Python 3.12 runtime Dockerfile.
- **Acceptance:** clean checkout installs from lock; service starts; format/lint/type/unit commands pass; runtime reports Python 3.12; CPMS has no OpenStackSDK dependency.

### CPMS-002 — Typed configuration and secret-safe logging

- **Sprint/Priority/Points:** 0 / Must / 5
- **Depends on:** CPMS-001
- **Tasks:** Pydantic settings, environment profiles, structured logging, correlation middleware, redaction filters, startup validation.
- **Acceptance:** missing required production config fails fast; password/token/authorization/`user_data` fields redact in tests; correlation ID is accepted or generated and returned.

### CPMS-003 — Health and local infrastructure integration

- **Sprint/Priority/Points:** 0 / Must / 3
- **Depends on:** CPMS-001
- **Tasks:** live/ready endpoints, PostgreSQL 18 and RabbitMQ checks, Compose documentation alignment.
- **Acceptance:** liveness is process-only; readiness becomes false when DB or RabbitMQ is unavailable; Valkey is not a CPMS readiness dependency.

### CPMS-004 — Local quality pipeline

- **Sprint/Priority/Points:** 0 / Must / 5
- **Depends on:** CPMS-001..003
- **Acceptance:** Husky pre-commit runs formatting, lint, typing, default tests, contract validation, and secret scan; infrastructure-backed gates are reserved for the GitLab pipeline.

## Epic CPMS-E1 — Contracts, persistence, and operations

### CPMS-101 — Canonical message envelope and schemas

- **Sprint/Priority/Points:** 1 / Must / 8
- **Depends on:** CPMS-001
- **Coordinates with:** OSPS-101
- **Tasks:** Pydantic models, JSON Schemas, schema-version rules, golden fixtures for command/progress/result/error/inventory batch, checksum manifest.
- **Acceptance:** all fixtures validate; unknown major version rejects; additive fields remain compatible; no event fixture contains credential/password/token.

### CPMS-102 — Common error and API response model

- **Sprint/Priority/Points:** 1 / Must / 5
- **Depends on:** CPMS-101
- **Acceptance:** validation, conflict, not-found, capability, provider, timeout, and internal errors use one safe envelope with stable codes and correlation ID.

### CPMS-103 — Initial database migration and unit of work

- **Sprint/Priority/Points:** 1 / Must / 8
- **Depends on:** CPMS-001
- **Tasks:** SQLAlchemy async engine/session, metadata conventions, provider/connection/credential/operation/event/inbox/outbox tables, Alembic baseline, repositories, transaction boundary.
- **Acceptance:** migration applies to empty PostgreSQL 18; constraints/indexes exist; rollback behavior is documented/tested; repository transaction tests pass.

### CPMS-104 — Operation state machine and immutable history

- **Sprint/Priority/Points:** 1 / Must / 8
- **Depends on:** CPMS-102, CPMS-103
- **Acceptance:** only valid transitions succeed; terminal states are immutable; every transition appends ordered event; concurrent update conflict is detected; safe actor context is preserved.

### CPMS-105 — Idempotent operation creation

- **Sprint/Priority/Points:** 1 / Must / 5
- **Depends on:** CPMS-104
- **Acceptance:** same key and semantic request returns existing operation; same key with different request returns 409; concurrent identical requests create one operation.

### CPMS-106 — Transactional outbox publisher and inbox consumer

- **Sprint/Priority/Points:** 1 / Must / 8
- **Depends on:** CPMS-101, CPMS-103
- **Acceptance:** operation/outbox commit atomically; publisher confirms before published state; retry schedule survives restart; inbox deduplicates by consumer/message; handler failure rolls back inbox/domain changes.

## Epic CPMS-E2 — Provider connection vertical slice

### CPMS-201 — Provider CRUD API

- **Sprint/Priority/Points:** 2 / Must / 5
- **Depends on:** CPMS-102, CPMS-103
- **Acceptance:** create/list/get/update provider; only supported provider type accepted; pagination/filter conventions apply; delete/disable behavior preserves referenced history.

### CPMS-202 — Encrypted credential lifecycle

- **Sprint/Priority/Points:** 2 / Must / 8
- **Depends on:** CPMS-103
- **Tasks:** encryption port/adapter, key versioning, create/update/delete metadata APIs, internal resolution service.
- **Acceptance:** plaintext never stored or returned publicly; rotation works; referenced credential cannot be deleted; wrong/missing key fails safely; redaction tests pass.

### CPMS-203 — Provider connection API and invariants

- **Sprint/Priority/Points:** 2 / Must / 8
- **Depends on:** CPMS-201, CPMS-202
- **Acceptance:** one connection captures one project/region and username/password scope; optimistic versioning works; public responses omit secrets; status starts pending.

### CPMS-204 — Internal credential resolution endpoint

- **Sprint/Priority/Points:** 2 / Must / 3
- **Depends on:** CPMS-202, CPMS-203
- **Coordinates with:** OSPS-202
- **Acceptance:** internal route resolves only a valid referenced credential and connection data; excluded from public ingress/OpenAPI grouping; request/response logs redact secrets.

### CPMS-205 — Async connection validation workflow

- **Sprint/Priority/Points:** 2 / Must / 8
- **Depends on:** CPMS-104..106, CPMS-203
- **Coordinates with:** OSPS-201..204
- **Acceptance:** endpoint returns 202 and operation; command uses reference only; progress/result updates operation; successful capabilities persist; auth/unavailable failures map correctly; replay is safe.

### CPMS-206 — Operation query APIs

- **Sprint/Priority/Points:** 2 / Must / 5
- **Depends on:** CPMS-104
- **Acceptance:** list/get/events support stable pagination/filtering; terminal result/error is safe; unknown operation returns normalized 404.

## Epic CPMS-E3 — Inventory and reconciliation

### CPMS-301 — Typed inventory schema and migrations

- **Sprint/Priority/Points:** 3 / Must / 13
- **Depends on:** CPMS-103
- **Tasks:** nine typed resource tables, instance-port/volume joins, lifecycle columns, provider identity and query indexes.
- **Acceptance:** uniqueness is per connection/resource table; relationships and soft delete work; migrations pass on PostgreSQL 18; representative query plans use intended indexes.

### CPMS-302 — Inventory sync and batch persistence

- **Sprint/Priority/Points:** 3 / Must / 8
- **Depends on:** CPMS-301, CPMS-106
- **Coordinates with:** OSPS-301..304
- **Acceptance:** batch deduplication and checksum rules work; out-of-order types persist; sequence conflict fails safely; unsupported collection is distinct from empty.

### CPMS-303 — Safe full-sync finalization

- **Sprint/Priority/Points:** 3 / Must / 13
- **Depends on:** CPMS-302
- **Acceptance:** only complete successful sync marks missing rows deleted; partial/failed/missing-last batch never deletes; relationships finalize; reappearing provider ID reactivates same CPMS UUID; one active full sync per connection.

### CPMS-304 — Inventory query APIs

- **Sprint/Priority/Points:** 3 / Must / 8
- **Depends on:** CPMS-301
- **Acceptance:** list/get all scoped resource types; default hides deleted; `include_deleted` works; allow-listed filters/sorts and uniform pagination work; provider attributes remain versioned.

### CPMS-305 — Manual full sync and targeted refresh APIs

- **Sprint/Priority/Points:** 3 / Must / 8
- **Depends on:** CPMS-302, CPMS-205
- **Coordinates with:** OSPS-301, OSPS-305
- **Acceptance:** endpoints create idempotent operations; duplicate full sync returns active operation; targeted not-found produces tombstone; provider timeout does not imply deletion.

## Epic CPMS-E4 — VM lifecycle

### CPMS-401 — VM create contract and validation

- **Sprint/Priority/Points:** 4 / Must / 8
- **Depends on:** CPMS-101, CPMS-304
- **Coordinates with:** OSPS-401
- **Acceptance:** validates flavor/image/network/port/security-group ownership; supports IMAGE and VOLUME_FROM_IMAGE; requires explicit network; accepts safe optional key pair/user data/config drive; never logs user data.

### CPMS-402 — VM create operation workflow

- **Sprint/Priority/Points:** 4 / Must / 8
- **Depends on:** CPMS-401, CPMS-105..106
- **Acceptance:** returns 202; publishes reference-only command; result atomically updates operation and normalized instance/relations; duplicate idempotency key cannot create two operations.

### CPMS-403 — VM detail and power/delete workflows

- **Sprint/Priority/Points:** 4 / Must / 8
- **Depends on:** CPMS-304, CPMS-105..106
- **Coordinates with:** OSPS-402..406
- **Acceptance:** detail/start/stop/reboot/delete use supported state/capability checks; result refreshes related inventory; delete creates tombstone; invalid state returns stable conflict.

### CPMS-404 — Root-volume lifecycle persistence

- **Sprint/Priority/Points:** 4 / Must / 5
- **Depends on:** CPMS-301, CPMS-402
- **Acceptance:** boot source and delete-on-termination persist; local root disappears with VM; created Cinder root follows requested policy; CPMS does not issue an independent blind volume delete.

## Epic CPMS-E5 — Scheduling, recovery, and release

### CPMS-501 — Inventory scheduler with jitter

- **Sprint/Priority/Points:** 5 / Should / 5
- **Depends on:** CPMS-305
- **Acceptance:** per-connection schedule creates the same workflow as manual sync; jitter prevents synchronized starts; disabled/invalid connections skip safely; no scheduler performs provider I/O.

### CPMS-502 — Operation timeout and late-result reconciliation

- **Sprint/Priority/Points:** 5 / Must / 8
- **Depends on:** CPMS-104, CPMS-106
- **Acceptance:** expired nonterminal operations become timed out with event; late result is retained without silently rewriting terminal state; reconciliation outcome is deterministic and observable.

### CPMS-503 — DLQ and outbox/inbox operational controls

- **Sprint/Priority/Points:** 5 / Must / 5
- **Depends on:** CPMS-106
- **Acceptance:** metrics expose backlog/redelivery/DLQ; safe replay procedure is documented/tested; poison messages cannot loop indefinitely; no payload secret is exposed.

### CPMS-504 — Observability and LMS-ready audit projection

- **Sprint/Priority/Points:** 5 / Should / 5
- **Depends on:** CPMS-104
- **Acceptance:** operation/correlation/provider/resource IDs propagate; metrics cover API/operation/sync/messaging; audit projection contains action/target/outcome/context without direct LMS dependency.

### CPMS-505 — End-to-end recovery acceptance

- **Sprint/Priority/Points:** 5 / Must / 13
- **Depends on:** all Must CPMS stories; paired OSPS stories
- **Acceptance:** approved eight-scenario real-OpenStack suite passes, including service restarts, message replay, direct drift, both boot modes, and no lost operation.

## Deferred backlog

- Keycloak authentication/authorization and service-to-service identity.
- MS organization/domain and TMS workspace/project integration.
- LMS audit event publisher.
- VMware provider service.
- Webhook/SSE operation notifications.
- OpenStack notification-driven refresh.
- Cursor pagination migration if offset performance becomes insufficient.
- Shared contracts package after a second provider justifies it.
