"""Expose mobile OTP authentication HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.entities import User
from app.schemas.auth import LoginResponse, MobileRequest, VerifyRequest, VerifyResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK, summary="Request a demo OTP")
async def login(payload: MobileRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> LoginResponse:
    """Begin the mobile login flow.

    Args:
        payload: Strictly validated mobile login request.
        session: The request database session.

    Returns:
        An OTP-required response.
    """
    return await AuthService(session).begin_login(payload.mobile_number)


@router.post("/verify", response_model=VerifyResponse, status_code=status.HTTP_200_OK, summary="Verify the demo OTP")
async def verify(payload: VerifyRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> VerifyResponse:
    """Verify an OTP and return a signed bearer credential.

    Args:
        payload: Strictly validated mobile and OTP request.
        session: The request database session.

    Returns:
        The signed bearer token response.
    """
    return await AuthService(session).verify_otp(payload.mobile_number, payload.otp)


@router.get("/session", response_model=MobileRequest, status_code=status.HTTP_200_OK, summary="Inspect the protected session")
async def session(current_user: Annotated[User, Depends(get_current_user)]) -> MobileRequest:
    """Return the currently authenticated mobile identity.

    Args:
        current_user: The bearer-authenticated persistent user.

    Returns:
        The authenticated user's mobile number.
    """
    return MobileRequest(mobile_number=current_user.mobile_number)
