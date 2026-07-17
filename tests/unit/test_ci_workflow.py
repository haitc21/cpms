"""CPMS-004: CI workflow acceptance checks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_defines_required_quality_gates() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    required = [
        "uv sync --frozen",
        "ruff format --check",
        "ruff check",
        "mypy",
        "pytest",
        "detect_secrets",
        "alembic upgrade head",
        "validate_contracts",
        "docker build",
        "postgres:",
        "rabbitmq:",
    ]
    missing = [item for item in required if item not in workflow]
    assert missing == [], f"CI workflow missing gates: {missing}"
