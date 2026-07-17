# CPMS

Cloud Provider Management Service — provider-neutral control plane for OpenStack
provider connections, credentials, inventory, and VM operations via OSPS.

## Requirements

- CPython 3.12 (do not use Python 3.14)
- [uv](https://github.com/astral-sh/uv) for locked installs
- Local infrastructure from `deploy/docker` (PostgreSQL 18, RabbitMQ 4.1)

## Setup

```powershell
py -3.12 -m uv sync --all-extras --frozen
```

## Run

```powershell
py -3.12 -m uv run cpms serve --host 127.0.0.1 --port 8000
py -3.12 -m uv run cpms worker --once
```

## Quality gates

```powershell
py -3.12 -m uv sync --frozen --all-extras
py -3.12 -m uv run ruff format --check src tests
py -3.12 -m uv run ruff check src tests
py -3.12 -m uv run mypy
py -3.12 -m uv run pytest -q
py -3.12 -m uv run alembic upgrade head
py -3.12 -m uv run python -m cpms.contracts.validate_contracts
py -3.12 -m uv run python -m detect_secrets scan --baseline .secrets.baseline --exclude-files "(?i)(.*\.venv/.*|.*uv\.lock$|.*\.git/.*)"
```

CI definition: `.github/workflows/ci.yml`.
