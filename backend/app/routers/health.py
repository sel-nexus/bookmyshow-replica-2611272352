"""Expose database-aware API health status."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=dict[str, str], status_code=status.HTTP_200_OK, summary="Check database readiness")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    """Execute a lightweight PostgreSQL query before declaring readiness.

    Args:
        session: The request database session.

    Returns:
        The process and database health status.
    """
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "up"}
