"""Coordinate mobile OTP authentication policy."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.repositories.users import UserRepository
from app.schemas.auth import LoginResponse, VerifyResponse


class InvalidOtpError(Exception):
    """Signal that the submitted OTP does not match the configured demo code."""


class AuthService:
    """Implement the demo mobile number and OTP flow."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the service to an async transaction session.

        Args:
            session: The request-scoped database session.
        """
        self._session = session
        self._users = UserRepository(session)

    async def begin_login(self, mobile_number: str) -> LoginResponse:
        """Return the next authentication state for a valid mobile number.

        Args:
            mobile_number: The validated mobile number.

        Returns:
            The OTP-required response envelope.
        """
        return LoginResponse(authentication_state="otp_required", mobile_number=mobile_number)

    async def verify_otp(self, mobile_number: str, otp: str) -> VerifyResponse:
        """Validate the demo OTP, persist the user, and issue a JWT.

        Args:
            mobile_number: The validated mobile number.
            otp: The submitted one-time password.

        Returns:
            The token response and inspected claims.

        Raises:
            InvalidOtpError: If the configured OTP does not match.
        """
        if otp != get_settings().demo_otp:
            raise InvalidOtpError()
        user = await self._users.get_or_create(mobile_number)
        await self._session.commit()
        await self._session.refresh(user)
        token, claims = create_access_token(user)
        return VerifyResponse(access_token=token, token_type="bearer",
                              expires_in=get_settings().jwt_expires_seconds, claims=claims)
