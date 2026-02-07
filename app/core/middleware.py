from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.request_context import set_request_id

logger = logging.getLogger("app.access")


class RequestIdLoggingMiddleware(BaseHTTPMiddleware):  # type: ignore
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = rid
        set_request_id(rid)

        t0 = time.perf_counter()
        response = await call_next(request)
        dt_ms = (time.perf_counter() - t0) * 1000.0

        response.headers["X-Request-Id"] = rid

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round(dt_ms, 3),
            },
        )
        return response
