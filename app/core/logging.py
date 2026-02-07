from __future__ import annotations

import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        rid = get_request_id()
        record.request_id = rid
        return True


def setup_logging(*, level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    formatter = JsonFormatter(fmt)
    handler.setFormatter(formatter)

    handler.addFilter(RequestIdFilter())

    root.handlers.clear()
    root.addHandler(handler)

    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel("WARNING")
