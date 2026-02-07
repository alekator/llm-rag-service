from __future__ import annotations

import logging
from typing import cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api.v1.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def _rid(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    vexc = cast(RequestValidationError, exc)

    rid = _rid(request)
    logger.warning("validation_error", extra={"request_id": rid, "errors": vexc.errors()})
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            request_id=rid,
            code="validation_error",
            message="Request validation failed",
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    rid = _rid(request)
    logger.exception("unhandled_error", extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            request_id=rid,
            code="internal_error",
            message="Internal server error",
        ).model_dump(),
    )
