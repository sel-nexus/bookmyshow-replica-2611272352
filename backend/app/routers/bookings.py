"""Expose authenticated booking confirmation creation."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.entities import User
from app.schemas.bookings import BookingConfirmationResponse, BookingCreateRequest
from app.services.bookings import BookingService

router = APIRouter(prefix="/api", tags=["bookings"])


@router.post("/bookings", response_model=BookingConfirmationResponse, status_code=status.HTTP_201_CREATED, summary="Create a paid booking confirmation")
async def create_booking(
    request: BookingCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BookingConfirmationResponse:
    """Persist an authenticated customer's fully server-validated booking.

    Args:
        request: The strict, minimal booking payload.
        user: The bearer-authenticated customer.
        session: The request-scoped PostgreSQL session.

    Returns:
        The durable server-generated booking confirmation.
    """
    return await BookingService(session).create_booking(user, request)
