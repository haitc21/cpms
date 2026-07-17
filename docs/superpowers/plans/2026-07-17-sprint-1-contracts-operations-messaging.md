# Sprint 1 Contracts, Operations, and Messaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver executable CPMS↔OSPS contracts, CPMS durable operation core (DB + state machine + idempotency + outbox/inbox), and OSPS robust RabbitMQ runtime with envelope validation—without provider CRUD, inventory sync, or OpenStack mutations.

**Architecture:** CPMS remains the canonical contract and PostgreSQL source of truth. OSPS is a stateless adapter that pins CPMS fixtures/checksums. Commands/events use a versioned envelope on durable RabbitMQ topic exchanges. CPMS writes operations and outbox rows in one transaction; a publisher confirms before marking published. CPMS consumes events through an inbox. OSPS validates envelopes before dispatch and never invents common fields.

**Tech Stack:** CPython 3.12, FastAPI/Pydantic v2, SQLAlchemy 2 + Alembic + Psycopg 3 (CPMS only), aio-pika 10.0.1, OpenStackSDK 4.17.0 present in OSPS but unused for mutations this sprint, uv lockfiles, pytest/ruff/mypy/detect-secrets.

## Global Constraints

- CPython `>=3.12,<3.13` only; never Python 3.14.
- CPMS must not depend on OpenStackSDK; OSPS must not add SQLAlchemy/Alembic/PostgreSQL/MongoDB/Valkey.
- Contract-first: failing fixture/contract tests before producer/consumer behavior.
- Secrets (password, token, Authorization, CA private material, `user_data`) never appear in fixtures, logs, events, or API responses.
- Unknown major `schema_version` → reject safely (DLQ / contract failure); additive minor fields tolerated.
- Topology defaults from design §10; names configurable via settings.
- No Sprint 2+ provider CRUD, inventory typed tables, or real OpenStack operations.
- Commits scoped per story or coherent vertical slice; no force push; no merge without review.
- Prefix supported commands with `rtk` where available.
- CodeGraph: prefer `codegraph_explore` when `.codegraph/` indexes CPMS/OSPS; otherwise note and use direct reads.

## ManageIQ / OpenStack assumptions (adopted, not copied)

| Source | Adopted idea | CPMS/OSPS translation |
|---|---|---|
| ManageIQ `MiqTask` / `Job` | Durable task status + message updates | `operations` + immutable `operation_events` |
| ManageIQ provider + authentication records | Separate config vs secrets | `providers` / `provider_connections` / `credentials` tables (encrypted later Sprint 2) |
| ManageIQ `ems_ref` | Provider identity ≠ internal UUID | Columns reserved on ops targets; inventory uniqueness deferred to Sprint 3 |
| ManageIQ queue workers | At-least-once work items | Outbox/inbox + OSPS replay-safe handlers (precondition stubs in Sprint 1) |
| OpenStackSDK exceptions | Map SDK hierarchy, keep request IDs | OSPS-103 normalization; no raw body leakage |
| Rejected | Rails AASM copy, EAV inventory, notification bus | Explicit enum transitions; typed tables later; RabbitMQ only |

## File map (create/modify)

### CPMS

| Path | Responsibility |
|---|---|
| `src/cpms/contracts/messages/envelope.py` | Pydantic envelope + version rules |
| `src/cpms/contracts/messages/types.py` | Message type constants |
| `src/cpms/contracts/errors.py` | Common error model |
| `src/cpms/contracts/api/responses.py` | API error/response envelope |
| `src/cpms/contracts/jsonschema/*.json` | Generated/exported JSON Schema |
| `src/cpms/contracts/fixtures/**/*.json` | Golden fixtures |
| `src/cpms/contracts/checksums.json` | SHA-256 manifest (via `write_manifest`) |
| `src/cpms/domain/operations/states.py` | State enum + transition table |
| `src/cpms/domain/operations/service.py` | Create/transition/idempotency rules |
| `src/cpms/infrastructure/db/models/*.py` | SQLAlchemy models |
| `src/cpms/infrastructure/db/unit_of_work.py` | Async session/UoW |
| `src/cpms/infrastructure/db/repositories/*.py` | Repositories |
| `alembic/versions/20260731_0001_sprint1_core.py` | Baseline migration |
| `src/cpms/infrastructure/messaging/outbox.py` | Outbox writer + publisher loop |
| `src/cpms/infrastructure/messaging/inbox.py` | Inbox consumer dedupe |
| `src/cpms/infrastructure/messaging/topology.py` | Exchange/queue declaration helpers |
| `tests/contract/**` | Fixture validation tests |
| `tests/unit/domain/**` | State machine / idempotency |
| `tests/integration/**` | Postgres + RabbitMQ |

### OSPS

| Path | Responsibility |
|---|---|
| `src/osps/contracts/**` | Pinned copy of CPMS schemas/fixtures/checksums |
| `src/osps/messaging/topology.py` | Declare durable topology |
| `src/osps/messaging/connection.py` | Robust connection factory |
| `src/osps/messaging/consumer.py` | Prefetch, manual ack, reconnect |
| `src/osps/messaging/publisher.py` | Publisher confirms |
| `src/osps/messaging/runtime.py` | Wire lifecycle + consume loop |
| `src/osps/openstack/errors.py` | Error normalization + retry class |
| `src/osps/application/dispatch.py` | Envelope validate → handler route |
| `src/osps/application/handlers/noop.py` | Sprint 1 noop handler for validated commands |
| `tests/contract/**` | Pin checksum + fixture validation |
| `tests/integration/**` | RabbitMQ topology/redelivery |

---

### Task 1: CPMS-101 — Canonical envelope and golden fixtures

**Files:**
- Create: `src/cpms/contracts/messages/envelope.py`
- Create: `src/cpms/contracts/messages/types.py`
- Create: `src/cpms/contracts/fixtures/commands/connection_validate.json`
- Create: `src/cpms/contracts/fixtures/events/operation_progress.json`
- Create: `src/cpms/contracts/fixtures/events/operation_completed.json`
- Create: `src/cpms/contracts/fixtures/events/operation_failed.json`
- Create: `src/cpms/contracts/fixtures/events/inventory_batch.json`
- Create: `src/cpms/contracts/jsonschema/message_envelope.schema.json`
- Modify: `src/cpms/contracts/checksums.json` via `python -m cpms.contracts.write_manifest`
- Test: `tests/contract/test_envelope_fixtures.py`

**Interfaces:**
- Produces: `class MessageEnvelope(BaseModel)` with fields matching design §10.1; `def parse_schema_version(v: str) -> tuple[int, int]`; `def assert_supported_major(v: str, supported_major: int = 1) -> None`
- Consumes: none

- [ ] **Step 1: Write the failing contract test**

```python
import json
from pathlib import Path
from cpms.contracts.messages.envelope import MessageEnvelope, assert_supported_major

FIXTURES = Path("src/cpms/contracts/fixtures")

def test_connection_validate_fixture_validates():
    raw = json.loads((FIXTURES / "commands/connection_validate.json").read_text())
    env = MessageEnvelope.model_validate(raw)
    assert env.message_type == "openstack.connection.validate"
    assert env.credential_reference is not None
    assert "password" not in json.dumps(raw)

def test_unknown_major_version_rejected():
    with pytest.raises(ValueError, match="unsupported major"):
        assert_supported_major("2.0")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk pytest tests/contract/test_envelope_fixtures.py -q`  
Expected: FAIL with `ModuleNotFoundError` or missing fixture path.

- [ ] **Step 3: Implement envelope + fixtures (no secrets)**

```python
class MessageEnvelope(BaseModel):
    message_id: UUID
    message_type: str
    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    occurred_at: datetime
    correlation_id: UUID
    causation_id: UUID | None = None
    operation_id: UUID
    idempotency_key: str | None = None
    provider_id: UUID
    provider_connection_id: UUID
    credential_reference: UUID | None = None
    trace_context: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
```

Golden fixture `connection_validate.json` uses synthetic UUIDs only; payload contains auth URL/project/region references—not passwords.

- [ ] **Step 4: Export JSON Schema and refresh checksum**

Run:
```powershell
py -3.12 -m uv run python -c "from cpms.contracts.messages.envelope import MessageEnvelope; Path('src/cpms/contracts/jsonschema/message_envelope.schema.json').write_text(MessageEnvelope.model_json_schema()|json)"
py -3.12 -m uv run python -m cpms.contracts.write_manifest
py -3.12 -m uv run python -m cpms.contracts.validate_contracts
```
Expected: `contracts ok (N fixtures)` with N ≥ 5.

- [ ] **Step 5: Run tests and commit**

Run: `rtk pytest tests/contract -q` → PASS  
Commit: `feat(CPMS-101): add canonical message envelope and golden fixtures`

---

### Task 2: OSPS-101 — Pin CPMS contracts

**Files:**
- Create/overwrite: `src/osps/contracts/**` as byte-for-byte pin of CPMS `jsonschema/`, `fixtures/`, `checksums.json`
- Test: `tests/contract/test_pinned_checksum.py`

**Interfaces:**
- Consumes: CPMS `checksums.json` after Task 1
- Produces: identical OSPS pin; `def assert_pin_matches_manifest() -> None`

- [ ] **Step 1: Failing test for checksum mismatch detection**

```python
def test_pinned_checksums_match_files():
    from osps.contracts.validate import validate_contract_tree
    result = validate_contract_tree()
    assert result.ok is True
    assert result.fixture_count >= 5
```

- [ ] **Step 2: Run — expect FAIL until pin copied**

- [ ] **Step 3: Copy pin from CPMS (PowerShell)**

```powershell
$src = "c:\work\Cloud\project\CMP\src\cpms\src\cpms\contracts"
$dst = "c:\work\Cloud\project\CMP\src\osps\src\osps\contracts"
Copy-Item "$src\checksums.json" "$dst\checksums.json" -Force
Copy-Item "$src\fixtures" "$dst\fixtures" -Recurse -Force
Copy-Item "$src\jsonschema" "$dst\jsonschema" -Recurse -Force
```

Do not edit fields in OSPS. Propose changes only in CPMS.

- [ ] **Step 4: Verify both validators**

Run: `rtk pytest tests/contract -q` in OSPS; `validate_contracts` in both → PASS  
Commit: `feat(OSPS-101): pin CPMS contract fixtures and checksum`

---

### Task 3: CPMS-102 — Common error and API response model

**Files:**
- Create: `src/cpms/contracts/errors.py`
- Create: `src/cpms/api/errors.py` (FastAPI exception handlers)
- Create: `src/cpms/contracts/fixtures/errors/provider_authentication_failed.json`
- Test: `tests/contract/test_error_fixtures.py`, `tests/unit/api/test_error_handlers.py`

**Interfaces:**
- Produces: `class CommonError(BaseModel)` per design §11; `class ApiErrorResponse(BaseModel)` with `error: CommonError`, `correlation_id: UUID`
- Maps validation → `INVALID_REQUEST`; unknown routes → stable not-found envelope

- [ ] **Step 1: Failing fixture + handler tests**

```python
def test_auth_error_fixture_has_no_secrets():
    raw = json.loads(Path("src/cpms/contracts/fixtures/errors/provider_authentication_failed.json").read_text())
    err = CommonError.model_validate(raw)
    assert err.code == "PROVIDER_AUTHENTICATION_FAILED"
    assert err.retryable is False
    assert "token" not in json.dumps(raw).lower() or "[REDACTED]" in json.dumps(raw)
```

- [ ] **Step 2: Run — FAIL missing module**

- [ ] **Step 3: Implement models + FastAPI handlers returning correlation ID**

- [ ] **Step 4: Refresh checksum; pytest contract+unit → PASS**

Commit: `feat(CPMS-102): add common error and API response envelopes`

---

### Task 4: CPMS-103 — Initial migration and unit of work

**Files:**
- Create: `src/cpms/infrastructure/db/base.py`, `models/provider.py`, `models/credential.py`, `models/connection.py`, `models/operation.py`, `models/messaging.py`
- Create: `src/cpms/infrastructure/db/unit_of_work.py`
- Create: `alembic/versions/20260731_0001_sprint1_core.py`
- Test: `tests/integration/test_migrations.py`, `tests/integration/test_unit_of_work.py`

**Interfaces:**
- Produces: async `UnitOfWork` with `session`, `commit()`, `rollback()`
- Tables (minimum columns):
  - `providers(id UUID PK, name, type, description, status, created_at, updated_at)`
  - `credentials(id UUID PK, key_version, ciphertext, created_at, updated_at, version)`
  - `provider_connections(id UUID PK, provider_id FK, credential_id FK, scope JSONB, status, capabilities JSONB, version, ...)`
  - `operations(id UUID PK, type, target_type, target_id, state, progress, request_safe JSONB, result_safe JSONB, error JSONB, provider_connection_id, idempotency_key, correlation_id, deadline_at, version, ...)`
  - `operation_events(id UUID PK, operation_id FK, sequence INT, old_state, new_state, details JSONB, message_id, created_at)` UNIQUE `(operation_id, sequence)`
  - `outbox_messages(id UUID PK, aggregate_type, aggregate_id, message_type, routing_key, payload JSONB, state, attempts, available_at, published_at, ...)`
  - `inbox_messages(id UUID PK, consumer_name, message_id, message_type, payload JSONB, state, error, received_at, processed_at)` UNIQUE `(consumer_name, message_id)`

- [ ] **Step 1: Failing migration test**

```python
@pytest.mark.integration
def test_alembic_upgrade_creates_operations_table():
    # run alembic upgrade head against Compose DB
    # assert information_schema has 'operations', 'outbox_messages', 'inbox_messages'
```

- [ ] **Step 2: Run with `CPMS_RUN_INTEGRATION=1` — FAIL missing revision**

- [ ] **Step 3: Write models + Alembic revision; upgrade empty DB**

Run: `py -3.12 -m uv run alembic upgrade head`  
Expected: creates tables/indexes/constraints on PostgreSQL 18.

- [ ] **Step 4: UoW rollback test passes**

Commit: `feat(CPMS-103): add sprint1 core schema migration and unit of work`

---

### Task 5: CPMS-104 — Operation state machine and history

**Files:**
- Create: `src/cpms/domain/operations/states.py`
- Create: `src/cpms/domain/operations/service.py`
- Create: `src/cpms/infrastructure/db/repositories/operations.py`
- Test: `tests/unit/domain/test_operation_transitions.py`, `tests/integration/test_operation_events.py`

**Interfaces:**
- Produces:
```python
class OperationState(StrEnum):
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"  # reserved; no public cancel API

ALLOWED: dict[OperationState, set[OperationState]] = {...}  # per design §9

class OperationService:
    async def transition(self, operation_id: UUID, new_state: OperationState, *, details: dict, message_id: UUID | None, actor_context: dict | None) -> Operation
```

- [ ] **Step 1: Failing unit tests for illegal transitions and terminal immutability**

```python
def test_succeeded_cannot_transition_to_running():
    assert OperationState.RUNNING not in ALLOWED[OperationState.SUCCEEDED]

def test_transition_appends_ordered_event():
    # arrange operation ACCEPTED
    # act transition QUEUED then RUNNING
    # assert events sequences 1,2 and states match
```

- [ ] **Step 2: FAIL — missing service**

- [ ] **Step 3: Implement transition guard + event append in same UoW; optimistic version conflict → domain error**

- [ ] **Step 4: Integration test concurrent update → one wins, one conflict**

Commit: `feat(CPMS-104): enforce operation state machine and event history`

---

### Task 6: CPMS-105 — Idempotent operation creation

**Files:**
- Modify: `src/cpms/domain/operations/service.py`
- Modify: migration if unique index not already present: `uq_operations_connection_type_idempotency`
- Test: `tests/integration/test_operation_idempotency.py`

**Interfaces:**
- Produces: `async def create_operation(..., idempotency_key: str, request_safe: dict) -> tuple[Operation, created: bool]`
- Same key + semantic equality → return existing; same key + different request → `IdempotencyKeyReusedError` (HTTP 409 later)

- [ ] **Step 1: Failing integration tests (duplicate same, duplicate different, concurrent)**

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement with DB uniqueness + request hash/canonical JSON compare**

- [ ] **Step 4: PASS under concurrent `asyncio.gather` creates**

Commit: `feat(CPMS-105): add idempotent operation creation`

---

### Task 7: CPMS-106 — Outbox publisher and inbox consumer skeleton

**Files:**
- Create: `src/cpms/infrastructure/messaging/topology.py`
- Create: `src/cpms/infrastructure/messaging/outbox.py`
- Create: `src/cpms/infrastructure/messaging/inbox.py`
- Modify: `src/cpms/messaging/runtime.py` to run publisher loop (not just connect)
- Test: `tests/integration/test_outbox_inbox.py`

**Interfaces:**
- Produces:
```python
async def enqueue_outbox(uow, *, message_type: str, routing_key: str, envelope: MessageEnvelope) -> None
async def publish_pending(batch_size: int = 50) -> int  # confirm then mark published
async def process_inbox(consumer_name: str, envelope: MessageEnvelope, handler) -> None
```
- Topology: declare exchanges/queues/bindings from design §10; durable + DLX.

- [ ] **Step 1: Failing tests**
  - operation create + outbox same transaction; rollback removes both
  - publisher marks published only after confirm
  - inbox duplicate `message_id` does not re-run handler

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement with `FOR UPDATE SKIP LOCKED`, aio-pika confirms, manual ack after DB commit on inbox**

- [ ] **Step 4: Integration against Compose RabbitMQ + Postgres → PASS**

Commit: `feat(CPMS-106): add transactional outbox publisher and inbox consumer`

---

### Task 8: OSPS-102 — RabbitMQ topology and robust runtime

**Files:**
- Create: `src/osps/messaging/topology.py`
- Create: `src/osps/messaging/connection.py`
- Create: `src/osps/messaging/consumer.py`
- Create: `src/osps/messaging/publisher.py`
- Modify: `src/osps/messaging/runtime.py`, `src/osps/messaging/lifecycle.py`
- Test: `tests/integration/test_rabbitmq_runtime.py`

**Interfaces:**
- Produces: `async def declare_topology(channel) -> None`; `class RobustConsumer`; publisher `await publish_event(envelope, routing_key)` with confirm before return
- Prefetch bounded (default 10); reconnect restores consumer; shutdown stops intake then drain/nack

- [ ] **Step 1: Failing integration tests for declare idempotency, confirm, nack→DLQ path**

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement; wire into `run_worker` long-running loop**

- [ ] **Step 4: PASS with Compose RabbitMQ**

Commit: `feat(OSPS-102): add durable RabbitMQ topology and robust runtime`

---

### Task 9: OSPS-103 — Error normalization and retry policy

**Files:**
- Create: `src/osps/openstack/errors.py`
- Create: `src/osps/openstack/retry.py`
- Test: `tests/unit/openstack/test_error_normalization.py`, `tests/unit/openstack/test_retry_policy.py`
- Pin: copy CPMS error fixtures if needed

**Interfaces:**
- Produces:
```python
def normalize_openstack_exception(exc: BaseException, *, service: str | None) -> CommonError
def classify_retry(error: CommonError) -> RetryDecision  # retryable, backoff, respect Retry-After
```
- Map SDK auth/forbidden/not-found/conflict/quota/rate-limit/timeout/network/5xx per design §11
- Never attach raw response body; keep `provider_request_id` when present

- [ ] **Step 1: Failing parametrized tests for each exception class → code/retryable**

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement mapping using `openstack.exceptions` hierarchy (import only; no live cloud)**

- [ ] **Step 4: PASS**

Commit: `feat(OSPS-103): normalize OpenStack errors and retry classification`

---

### Task 10: OSPS-104 — Handler dispatch and envelope validation

**Files:**
- Create: `src/osps/application/dispatch.py`
- Create: `src/osps/application/handlers/base.py`
- Create: `src/osps/application/handlers/noop.py`
- Modify: consumer to call dispatcher before ack
- Test: `tests/unit/application/test_dispatch.py`, `tests/integration/test_command_dispatch.py`

**Interfaces:**
- Produces:
```python
class Handler(Protocol):
    async def handle(self, envelope: MessageEnvelope) -> MessageEnvelope | None  # optional event

class Dispatcher:
    def register(self, message_type: str, handler: Handler) -> None
    async def dispatch(self, raw: bytes) -> None  # validate → route → publish result events
```
- Malformed/unsupported major version → nack to DLQ without handler invocation
- Progress/result must set causation/correlation/operation IDs from command

- [ ] **Step 1: Failing tests — malformed envelope never calls handler; happy path noop publishes completed event fixture shape**

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement validation-first dispatch**

- [ ] **Step 4: Integration round-trip with CPMS golden command fixture → PASS**

Commit: `feat(OSPS-104): add envelope validation and handler dispatch`

---

### Task 11: Sprint verification and demo

- [ ] **Step 1: Full CPMS DoD**

```powershell
cd c:\work\Cloud\project\CMP\src\cpms
py -3.12 -m uv sync --frozen --all-extras
py -3.12 -m uv run ruff format --check src tests
py -3.12 -m uv run ruff check src tests
py -3.12 -m uv run mypy
$env:CPMS_RUN_INTEGRATION="1"
py -3.12 -m uv run pytest -q
py -3.12 -m uv run alembic upgrade head
py -3.12 -m uv run python -m cpms.contracts.validate_contracts
py -3.12 -m uv run python -m detect_secrets scan --baseline .secrets.baseline --exclude-files "(?i)(.*\.venv/.*|.*uv\.lock$|.*\.git/.*)"
rtk git diff --check
rtk docker build -t cpms:sprint1 .
```

Expected: all green; fixtures validate; migration clean on empty DB.

- [ ] **Step 2: Full OSPS DoD** (same pattern with `OSPS_RUN_INTEGRATION=1`; no alembic)

- [ ] **Step 3: Demo scenario (local Compose; optional real OpenStack only for connectivity smoke if available—not required for Sprint 1 exit)**
  1. Start Compose postgres/rabbitmq.
  2. Run CPMS API + worker; run OSPS worker.
  3. Insert/create a synthetic operation that enqueues `openstack.connection.validate` outbox message (test harness or temporary internal call).
  4. Observe OSPS consume, validate envelope, dispatch noop, publish `cloud.operation.completed` (or progress) event.
  5. Observe CPMS inbox dedupe on redelivery.
  6. Confirm logs/fixtures contain no secrets.

- [ ] **Step 4: Update `plan/sprints/sprint-1.md` evidence in both repos; commit docs**

---

## Commit boundary summary

| Order | Commit | Repo |
|---|---|---|
| 1 | CPMS-101 fixtures+envelope | cpms |
| 2 | OSPS-101 pin | osps |
| 3 | CPMS-102 errors | cpms |
| 4 | CPMS-103 migration/UoW | cpms |
| 5 | CPMS-104 state machine | cpms |
| 6 | CPMS-105 idempotency | cpms |
| 7 | CPMS-106 outbox/inbox | cpms |
| 8 | OSPS-102 RabbitMQ runtime | osps |
| 9 | OSPS-103 errors/retry | osps |
| 10 | OSPS-104 dispatch | osps |
| 11 | Sprint evidence | both |

## Self-review

**1. Spec coverage**
- Design §10 envelope/topology/outbox/inbox → Tasks 1,7,8,10
- Design §11 errors/retry → Tasks 3,9
- Design §9 operations/events → Tasks 5,6
- Design §14 core tables (non-inventory) → Task 4
- Backlog CPMS-101..106 / OSPS-101..104 → all mapped
- Explicitly out of scope: provider CRUD, inventory tables, OpenStack mutations, Keycloak/TMS/LMS

**2. Placeholder scan:** no TBD/TODO left in task steps; commands and expected results included.

**3. Type consistency:** `MessageEnvelope`, `CommonError`, `OperationState`, `UnitOfWork`, `Dispatcher` names reused consistently across tasks.

**4. CodeGraph note:** CMP workspace index currently surfaces ManageIQ/OpenStackSDK/BMS symbols, not CPMS/OSPS package sources. Discovery for implementation should use direct reads under `cpms/src` and `osps/src` until those trees are indexed.
