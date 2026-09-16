"""Exercise authenticated catalogue HTTP behavior against real PostgreSQL."""

import asyncio
import os
from uuid import uuid4

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres"
os.environ["DB_NAME"] = "bookmyshow_test"
os.environ["JWT_SECRET"] = "bookmyshow-test-signing-secret-that-is-long-enough"
os.environ["JWT_ISSUER"] = "bookmyshow-api"
os.environ["JWT_AUDIENCE"] = "bookmyshow-web"
os.environ["DEMO_OTP"] = "1234"

import httpx
import pytest
import pytest_asyncio

from app.core.database import AsyncSessionFactory, engine, ensure_database_exists
from app.core.seed import seed_database
from app.main import app
from app.models.entities import Base


@pytest.fixture(scope="module", autouse=True)
def postgres_schema() -> None:
    """Provision a fresh real PostgreSQL schema and idempotent catalogue seed."""
    async def prepare() -> None:
        await ensure_database_exists()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        async with AsyncSessionFactory() as session:
            await seed_database(session)

    asyncio.run(prepare())


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    """Provide an in-process client that exercises the real HTTP surface."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


async def authorization_headers(client: httpx.AsyncClient) -> dict[str, str]:
    """Issue a genuine bearer token through the auth HTTP endpoint."""
    response = await client.post("/api/auth/verify", json={"mobile_number": "9876543210", "otp": "1234"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_movies_requires_bearer_token(client: httpx.AsyncClient) -> None:
    """Reject unauthenticated catalogue reads with the shared error shape."""
    response = await client.get("/api/movies")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
    assert response.headers["X-Correlation-ID"]


@pytest.mark.asyncio
async def test_movies_returns_required_titles_in_title_order(client: httpx.AsyncClient) -> None:
    """Return the seeded persisted titles ordered by the database query."""
    response = await client.get("/api/movies", headers=await authorization_headers(client))
    assert response.status_code == 200
    movies = response.json()["movies"]
    assert [movie["title"] for movie in movies] == ["Bloody Romeo", "OG2", "Paradise"]
    assert [movie["poster_placeholder"] for movie in movies] == ["/assets/posters/bloody-romeo.svg", "/assets/posters/og2.svg", "/assets/posters/paradise.svg"]


@pytest.mark.asyncio
async def test_theatres_returns_only_persisted_mappings(client: httpx.AsyncClient) -> None:
    """Filter theatre results through approved movie-theatre rows."""
    headers = await authorization_headers(client)
    movies = (await client.get("/api/movies", headers=headers)).json()["movies"]
    paradise_id = next(movie["id"] for movie in movies if movie["title"] == "Paradise")
    response = await client.get("/api/theatres", params={"movie_id": paradise_id}, headers=headers)
    assert response.status_code == 200
    assert [theatre["name"] for theatre in response.json()["theatres"]] == ["Sandhya 70mm", "Sudharsham 70mm"]


@pytest.mark.asyncio
async def test_theatres_reports_unknown_and_malformed_movie_ids(client: httpx.AsyncClient) -> None:
    """Return distinct stable domain errors for unknown and malformed IDs."""
    headers = await authorization_headers(client)
    unknown = await client.get("/api/theatres", params={"movie_id": str(uuid4())}, headers=headers)
    malformed = await client.get("/api/theatres", params={"movie_id": "not-a-uuid"}, headers=headers)
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "MOVIE_NOT_FOUND"
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "INVALID_MOVIE_ID"
    assert malformed.headers["X-Correlation-ID"]
