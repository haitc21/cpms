"""FastAPI application factory for CPMS."""

from __future__ import annotations

from fastapi import FastAPI

from cpms.api.errors import register_error_handlers
from cpms.api.health import router as health_router
from cpms.config import Settings, get_settings
from cpms.infrastructure.health import HealthChecks
from cpms.observability.logging import configure_logging
from cpms.observability.middleware import CorrelationIdMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the CPMS ASGI application."""
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, service_name=resolved.service_name)

    app = FastAPI(title="CPMS", version="0.1.0")
    app.state.settings = resolved
    app.state.health_checks = HealthChecks(resolved)
    app.add_middleware(CorrelationIdMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    return app
