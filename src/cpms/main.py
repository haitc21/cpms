"""FastAPI application factory for CPMS."""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the CPMS ASGI application."""
    app = FastAPI(title="CPMS", version="0.1.0")
    return app
