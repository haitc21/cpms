"""FastAPI application factory for CPMS."""

from __future__ import annotations

from fastapi import FastAPI

from cpms.config import Settings, get_settings
from cpms.observability.logging import configure_logging
from cpms.observability.middleware import CorrelationIdMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the CPMS ASGI application."""
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, service_name=resolved.service_name)

    app = FastAPI(title="CPMS", version="0.1.0")
    app.state.settings = resolved
    app.add_middleware(CorrelationIdMiddleware)
    return app
