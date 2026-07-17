# Sprint 1 — Stable contracts and durable operation core

**Dates:** 2026-07-31 to 2026-08-14  
**Capacity:** focused contract + persistence + messaging core  
**Sprint Goal:** CPMS owns executable common message/API contracts with golden fixtures and checksums; persists providers/connections/credentials/operations with an enforceable state machine and transactional outbox/inbox skeleton; OSPS pins those contracts and runs a robust RabbitMQ consumer/publisher with envelope validation, error normalization, and retry classification—without provider mutations yet.

## Selected stories

| Story | Points | Owner | OSPS dependency | Status |
|---|---:|---|---|---|
| CPMS-101 | 8 | Unassigned | OSPS-101 | Ready |
| CPMS-102 | 5 | Unassigned | OSPS-103 (error envelope) | Ready |
| CPMS-103 | 8 | Unassigned | none | Ready |
| CPMS-104 | 8 | Unassigned | none | Ready |
| CPMS-105 | 5 | Unassigned | none | Ready |
| CPMS-106 | 8 | Unassigned | OSPS-102 | Ready |

**Total:** 42 points (Must)

## Delivery order (contract-first)

1. CPMS-101 → OSPS-101 (pin immediately after checksum exists)
2. CPMS-102 → shared error fixtures used by OSPS-103
3. CPMS-103 → CPMS-104 → CPMS-105
4. CPMS-106 ∥ OSPS-102 (topology first on OSPS; outbox/inbox on CPMS)
5. OSPS-103 → OSPS-104

## Delivery tasks

- [ ] Confirm design §10–§14 for envelope, topology, DB tables, and errors.
- [ ] Add failing contract tests and golden fixtures before handlers.
- [ ] Land Alembic baseline for provider/ops/messaging tables on PostgreSQL 18.
- [ ] Implement operation transitions + idempotency with concurrency tests.
- [ ] Implement outbox/inbox with confirm-before-ack semantics.
- [ ] Coordinate OSPS pin + RabbitMQ runtime + envelope dispatch.
- [ ] Verify redaction: no password/token/`user_data` in fixtures or events.
- [ ] Run Definition of Done quality gates; update this backlog evidence.

## Risks and impediments

| Risk/impediment | Owner | Mitigation | Status |
|---|---|---|---|
| Contract drift between repos | Joint | CPMS checksum first; OSPS pin in same sprint; CI validates both | Open |
| 42 points exceeds capacity | Joint | Keep Sprint 1 strictly foundation; defer inventory/provider APIs | Open |
| Windows asyncio/psycopg | CPMS | Keep SelectorEventLoop policy; sync probes where needed | Open |
| Outbox publisher races | CPMS | DB unique + `FOR UPDATE SKIP LOCKED` + confirm before mark published | Open |

## Review evidence

- Demo scenario: _(fill at review)_ create operation via domain service, outbox publishes command fixture validated by OSPS consumer stub; event inbox dedupes duplicate `message_id`.
- Test/migration commands and results: _(fill at review)_
- Contract checksum: _(fill at review)_
- Known limitations: no public provider CRUD yet; no OpenStack provider calls; no inventory tables.

## Retrospective actions

- Keep: _(fill)_
- Improve: _(fill)_
- One measurable action for next sprint: _(fill)_

## Implementation plan

Canonical: `docs/superpowers/plans/2026-07-17-sprint-1-contracts-operations-messaging.md`
