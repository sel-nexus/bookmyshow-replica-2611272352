"""Issue and validate JWT bearer credentials."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.entities import User
from app.repositories.users import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticationRequiredError(Exception):
    """Signal a generic bearer authentication failure."""


def create_access_token(user: User) -> tuple[str, dict[str, str | int]]:
    """Sign a short-lived JWT for the supplied persisted user.

    Args:
        user: The user whose UUID becomes the subject claim.

    Returns:
        The compact JWT and its response-safe claims.
    """
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(seconds=settings.jwt_expires_seconds)
    claims: dict[str, str | int] = {
        "sub": str(user.id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256"), claims


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Resolve and validate the authenticated request user.

    Args:
        request: The current HTTP request.
        credentials: Parsed bearer authorization credentials.
        session: The request-scoped database session.

    Returns:
        The persisted authenticated user.

    Raises:
        AuthenticationRequiredError: If the token is missing, invalid, expired, or stale.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationRequiredError()
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"],
                             issuer=settings.jwt_issuer, audience=settings.jwt_audience,
                             options={"require": ["sub", "iss", "aud", "iat", "exp"]})
    except jwt.PyJWTError as error:
        raise AuthenticationRequiredError() from error
    user = await session.get(User, payload.get("sub"))
    if user is None or str(user.id) != payload.get("sub"): 
        raise AuthenticationRequiredError()
    request.state.current_user = user
    return user
