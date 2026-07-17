"""CPMS command-line entrypoints."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cpms", description="Cloud Provider Management Service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the CPMS HTTP API")
    serve.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve.add_argument("--port", type=int, default=8000, help="Bind port")

    worker = subparsers.add_parser("worker", help="Run the CPMS background worker")
    worker.add_argument(
        "--once",
        action="store_true",
        help="Connect once to RabbitMQ and exit (smoke mode)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    from cpms.runtime import configure_event_loop_policy

    configure_event_loop_policy()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "serve":
        import uvicorn

        uvicorn.run("cpms.main:create_app", factory=True, host=args.host, port=args.port)
        return

    if args.command == "worker":
        from cpms.config import get_settings
        from cpms.messaging.lifecycle import WorkerLifecycle
        from cpms.messaging.runtime import run_worker
        from cpms.observability.logging import configure_logging

        settings = get_settings()
        configure_logging(level=settings.log_level, service_name=settings.service_name)
        lifecycle = WorkerLifecycle()
        asyncio.run(run_worker(settings=settings, lifecycle=lifecycle, once=args.once))
        if args.once:
            print("cpms worker initialized", flush=True)
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main(sys.argv[1:])
