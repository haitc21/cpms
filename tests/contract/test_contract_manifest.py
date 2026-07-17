"""Sprint 0 empty-safe contract validation gate."""

from __future__ import annotations

from cpms.contracts.validate import validate_contract_tree


def test_contract_tree_validates_when_empty_or_consistent() -> None:
    result = validate_contract_tree()
    assert result.ok is True
    assert result.fixture_count >= 0
