from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    request_id: str
    code: str
    message: str
