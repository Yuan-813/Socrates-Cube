"""Health check route."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["系统"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "Socrates-Cube"}
