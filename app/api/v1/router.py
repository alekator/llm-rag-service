from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.query import router as query_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(documents_router, tags=["documents"])
router.include_router(query_router, tags=["query"])
router.include_router(health_router, tags=["health"])
