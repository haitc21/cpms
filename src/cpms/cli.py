"""CPMS command-line entrypoints."""

from __future__ import annotations

import argparse
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
        help="Initialize worker dependencies once and exit (smoke mode)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "serve":
        import uvicorn

        uvicorn.run("cpms.main:create_app", factory=True, host=args.host, port=args.port)
        return

    if args.command == "worker":
        if args.once:
            print("cpms worker initialized", flush=True)
            return
        print("cpms worker running", flush=True)
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main(sys.argv[1:])
