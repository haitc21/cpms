"""Database URL helper tests."""

from __future__ import annotations

from cpms.infrastructure.db import to_psycopg_conninfo


def test_to_psycopg_conninfo_strips_sqlalchemy_driver() -> None:
    assert (
        to_psycopg_conninfo("postgresql+psycopg://cpms:secret@127.0.0.1:5432/cpms")
        == "postgresql://cpms:secret@127.0.0.1:5432/cpms"
    )
