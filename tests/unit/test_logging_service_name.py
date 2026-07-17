"""service_name must appear in structured log output."""

from __future__ import annotations

import json
import logging
from io import StringIO

from cpms.observability.logging import configure_logging


def test_configure_logging_applies_custom_service_name() -> None:
    stream = StringIO()
    configure_logging(level="INFO", service_name="custom-cpms")
    root = logging.getLogger()
    assert root.handlers, "configure_logging must install a handler"
    root.handlers[0].setStream(stream)

    logging.getLogger("cpms.test").info("hello")

    payload = json.loads(stream.getvalue().strip())
    assert payload["service"] == "custom-cpms"
    assert payload["message"] == "hello"
