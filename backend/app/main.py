"""Create the BookMyShow authentication API application."""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, ensure_database_exists
from app.core.security import AuthenticationRequiredError
from app.core.seed import seed_database
from app.schemas.common import ErrorDetail, ErrorResponse
from app.services.auth import InvalidOtpError
from app.services.catalogue import MovieNotFoundError
from app.routers.auth import router as auth_router
from app.routers.catalogue import InvalidMovieIdError, router as catalogue_router
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    """Build a correlation-aware structured error response.

    Args:
        request: The failing HTTP request.
        status_code: The HTTP status to return.
        code: The stable machine-readable error code.
        message: The safe public error message.

    Returns:
        The structured JSON error response.
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message, correlation_id=correlation_id))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Provision the application database and apply committed migrations.

    Yields:
        Control to the running FastAPI application.
    """
    await ensure_database_exists()
    alembic_config = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_config, "head")
    async with AsyncSessionFactory() as session:
        await seed_database(session)
    yield


app = FastAPI(title="BookMyShow Replica API", version="1.0.0", description="Mobile OTP authentication API", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"])


@app.middleware("http")
async def attach_correlation_id(request: Request, call_next: object) -> JSONResponse:
    """Attach a correlation identifier to every response and error.

    Args:
        request: The inbound request.
        call_next: The next ASGI handler.

    Returns:
        The handler response decorated with the correlation ID.
    """
    request.state.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    response = await call_next(request)  # type: ignore[operator]
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
    """Translate strict request validation to the shared mobile error contract.

    Args:
        request: The rejected request.
        _: The validation details retained server-side.

    Returns:
        The structured malformed-mobile response.
    """
    return error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_MOBILE", "Invalid mobile number")


@app.exception_handler(InvalidOtpError)
async def invalid_otp_error(request: Request, _: InvalidOtpError) -> JSONResponse:
    """Translate demo OTP failure to a generic authentication response.

    Args:
        request: The rejected request.
        _: The domain error.

    Returns:
        The structured invalid-OTP response.
    """
    return error_response(request, status.HTTP_401_UNAUTHORIZED, "INVALID_OTP", "Invalid OTP")


@app.exception_handler(AuthenticationRequiredError)
async def authentication_required_error(request: Request, _: AuthenticationRequiredError) -> JSONResponse:
    """Translate bearer failures without exposing token validation details.

    Args:
        request: The rejected request.
        _: The authentication error.

    Returns:
        The structured authentication-required response.
    """
    return error_response(request, status.HTTP_401_UNAUTHORIZED, "AUTH_REQUIRED", "Authentication required")


@app.exception_handler(InvalidMovieIdError)
async def invalid_movie_id_error(request: Request, _: InvalidMovieIdError) -> JSONResponse:
    """Translate malformed movie identifiers to the catalogue error contract."""
    return error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_MOVIE_ID", "Invalid movie ID")


@app.exception_handler(MovieNotFoundError)
async def movie_not_found_error(request: Request, _: MovieNotFoundError) -> JSONResponse:
    """Translate missing catalogue movies to a structured not-found response."""
    return error_response(request, status.HTTP_404_NOT_FOUND, "MOVIE_NOT_FOUND", "Movie not found")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
    """Log database faults and return a safe readiness-style error.

    Args:
        request: The request that encountered a database fault.
        error: The database exception to log.

    Returns:
        The structured service-unavailable response.
    """
    logger.error("Database request failed: %s", type(error).__name__)
    return error_response(request, status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database unavailable")


app.include_router(auth_router)
app.include_router(catalogue_router)
app.include_router(health_router)
