"""Contract validation must not auto-create missing manifests."""

from __future__ import annotations

import json
from pathlib import Path

from cpms.contracts.validate import (
    ValidationResult,
    validate_contract_tree,
    write_contract_manifest,
)


def test_validate_fails_when_manifest_missing(tmp_path: Path) -> None:
    (tmp_path / "fixtures").mkdir()
    result = validate_contract_tree(tmp_path)
    assert result.ok is False
    assert "missing" in result.message.lower()
    assert not (tmp_path / "checksums.json").exists()


def test_write_manifest_creates_checksums_file(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / "example.json").write_text("{}", encoding="utf-8")

    result = write_contract_manifest(tmp_path)
    assert result.ok is True
    manifest = json.loads((tmp_path / "checksums.json").read_text(encoding="utf-8"))
    assert "fixtures/example.json" in manifest["fixtures"]

    validated = validate_contract_tree(tmp_path)
    assert validated == ValidationResult(ok=True, fixture_count=1, message="")
