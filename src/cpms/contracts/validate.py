"""Contract tree validation helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = CONTRACTS_ROOT / "checksums.json"


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    fixture_count: int
    message: str = ""


def _compute_fixture_checksums(base: Path) -> dict[str, str]:
    fixtures_dir = base / "fixtures"
    if not fixtures_dir.exists():
        return {}
    fixture_files = sorted(
        path for path in fixtures_dir.rglob("*") if path.is_file() and path.name != ".gitkeep"
    )
    return {
        path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in fixture_files
    }


def validate_contract_tree(root: Path | None = None) -> ValidationResult:
    """Validate fixture checksums against a committed manifest (read-only)."""
    base = root or CONTRACTS_ROOT
    manifest_path = base / "checksums.json"
    computed = _compute_fixture_checksums(base)

    if not manifest_path.exists():
        return ValidationResult(
            ok=False,
            fixture_count=len(computed),
            message="missing checksums.json",
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("fixtures", {})
    if expected != computed:
        return ValidationResult(
            ok=False,
            fixture_count=len(computed),
            message="contract checksum mismatch",
        )
    return ValidationResult(ok=True, fixture_count=len(computed))


def write_contract_manifest(root: Path | None = None) -> ValidationResult:
    """Create or refresh checksums.json from the current fixtures tree."""
    base = root or CONTRACTS_ROOT
    fixtures_dir = base / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    computed = _compute_fixture_checksums(base)
    manifest_path = base / "checksums.json"
    manifest_path.write_text(
        json.dumps({"fixtures": computed}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ValidationResult(
        ok=True,
        fixture_count=len(computed),
        message="manifest written",
    )


def main() -> None:
    result = validate_contract_tree()
    if not result.ok:
        raise SystemExit(f"contract validation failed: {result.message}")
    print(f"contracts ok ({result.fixture_count} fixtures)")


if __name__ == "__main__":
    main()
