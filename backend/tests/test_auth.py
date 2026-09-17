"""Exercise authentication HTTP behavior against real PostgreSQL."""

import asyncio
import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres"
os.environ["DB_NAME"] = "bookmyshow_test"
os.environ["JWT_SECRET"] = "bookmyshow-test-signing-secret-that-is-long-enough"
os.environ["JWT_ISSUER"] = "bookmyshow-api"
os.environ["JWT_AUDIENCE"] = "bookmyshow-web"
os.environ["DEMO_OTP"] = "1234"

import httpx
import jwt
import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.models.entities import User

from app.core.database import AsyncSessionFactory, engine, ensure_database_exists
from app.main import app
from app.models.entities import Base


@pytest.fixture(scope="module", autouse=True)
def postgres_schema() -> None:
    """Provision and reset the real PostgreSQL test schema."""
    async def prepare() -> None:
        await ensure_database_exists()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(prepare())


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    """Provide a real in-process HTTP client with app lifespan startup.

    Yields:
        An HTTP client exercising the full ASGI application.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


@pytest.mark.asyncio
async def test_login_accepts_trimmed_ten_digit_mobile(client: httpx.AsyncClient) -> None:
    """Return OTP-required for exactly ten trimmed ASCII digits."""
    response = await client.post("/api/auth/login", json={"mobile_number": " 9876543210 "})
    assert response.status_code == 200
    assert response.json() == {"authentication_state": "otp_required", "mobile_number": "9876543210"}


@pytest.mark.asyncio
async def test_login_rejects_malformed_or_unknown_fields(client: httpx.AsyncClient) -> None:
    """Return structured invalid-mobile errors for malformed strict payloads."""
    response = await client.post("/api/auth/login", json={"mobile_number": "12345abcde", "extra": True})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_MOBILE"
    assert response.json()["error"]["correlation_id"]


@pytest.mark.asyncio
async def test_verify_rejects_wrong_otp(client: httpx.AsyncClient) -> None:
    """Return the specified error without creating a user for a bad OTP."""
    response = await client.post("/api/auth/verify", json={"mobile_number": "9876543210", "otp": "0000"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_OTP"


@pytest.mark.asyncio
async def test_verify_persists_user_and_returns_exact_public_shape(client: httpx.AsyncClient) -> None:
    """Persist a user, expose only its public identity, and issue a valid JWT."""
    response = await client.post("/api/auth/verify", json={"mobile_number": "9876543210", "otp": "1234"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert set(body["user"]) == {"id", "mobile_number"}
    assert body["user"]["mobile_number"] == "9876543210"
    claims = jwt.decode(body["access_token"], os.environ["JWT_SECRET"], algorithms=["HS256"],
                        issuer="bookmyshow-api", audience="bookmyshow-web")
    assert claims["sub"] == body["user"]["id"]
    async with AsyncSessionFactory() as session:
        persisted_count = await session.scalar(select(func.count()).select_from(User).where(User.mobile_number == "9876543210"))
    assert persisted_count == 1


@pytest.mark.asyncio
async def test_database_rejects_direct_non_ascii_mobile_insert() -> None:
    """Enforce the mobile constraint even when application validation is bypassed."""
    await engine.dispose()
    async with AsyncSessionFactory() as session:
        session.add(User(mobile_number="١٢٣٤٥٦٧٨٩٠"))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {},
    {"mobile_number": None, "otp": "1234"},
    {"mobile_number": 9876543210, "otp": "1234"},
    {"mobile_number": "12345abcde", "otp": "1234"},
    {"mobile_number": "9" * 11, "otp": "1234"},
    {"mobile_number": "9876543210", "otp": None},
    {"mobile_number": "9876543210", "otp": "x" * 33},
    {"mobile_number": "9876543210", "otp": "1234", "role": "admin'; DROP TABLE users; --"},
])
async def test_verify_rejects_invalid_or_hostile_payload_without_creating_user(
    client: httpx.AsyncClient, payload: dict[str, object]
) -> None:
    """Reject invalid boundary and hostile inputs without leaking details or persisting users."""
    before: int
    async with AsyncSessionFactory() as session:
        before = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    response = await client.post("/api/auth/verify", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"INVALID_MOBILE", "INVALID_REQUEST"}
    assert "traceback" not in response.text.lower()
    async with AsyncSessionFactory() as session:
        after = await session.scalar(select(func.count()).select_from(User))
    assert after == before


@pytest.mark.asyncio
async def test_protected_session_rejects_missing_and_bad_tokens(client: httpx.AsyncClient) -> None:
    """Reject absent and malformed credentials with generic auth-required errors."""
    missing = await client.get("/api/auth/session")
    bad = await client.get("/api/auth/session", headers={"Authorization": "Bearer not-a-jwt"})
    assert missing.status_code == 401
    assert bad.status_code == 401
    assert missing.json()["error"]["code"] == "AUTH_REQUIRED"
    assert bad.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_health_executes_against_real_database(client: httpx.AsyncClient) -> None:
    """Report database readiness after a live SELECT statement."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
