"""Versioned message envelope shared by CPMS and OSPS."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def parse_schema_version(version: str) -> tuple[int, int]:
    parts = version.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"invalid schema version: {version}")
    return int(parts[0]), int(parts[1])


def assert_supported_major(version: str, *, supported_major: int = 1) -> None:
    major, _minor = parse_schema_version(version)
    if major != supported_major:
        raise ValueError(f"unsupported major schema version: {version}")


class MessageEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: UUID
    message_type: str = Field(min_length=1)
    schema_version: str
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

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        assert_supported_major(value)
        return value
