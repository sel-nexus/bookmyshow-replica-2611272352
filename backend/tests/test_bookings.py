"""Exercise durable booking confirmation behavior against real PostgreSQL."""

import asyncio
import os
from decimal import Decimal
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
from sqlalchemy import func, select

from app.core.database import AsyncSessionFactory, engine, ensure_database_exists
from app.core.seed import seed_database
from app.main import app
from app.models.entities import Base, Booking, Movie, Theatre, User
from app.schemas.bookings import BookingCreateRequest
from app.services.bookings import (BookingService, InvalidFixedSeatsError, InvalidPaymentMethodError,
                                   InvalidTheatreForMovieError, MovieNotFoundForBookingError, TheatreNotFoundError)


@pytest.fixture(scope="module", autouse=True)
def postgres_schema() -> None:
    """Reset the real PostgreSQL schema and seed its catalogue."""
    async def prepare() -> None:
        await ensure_database_exists()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        async with AsyncSessionFactory() as session:
            await seed_database(session)
        await engine.dispose()
    asyncio.run(prepare())


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    """Yield an in-process HTTP client backed by PostgreSQL."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    await engine.dispose()


async def headers(client: httpx.AsyncClient) -> dict[str, str]:
    """Issue a bearer token over the real auth HTTP surface."""
    response = await client.post("/api/auth/verify", json={"mobile_number": "9876543210", "otp": "1234"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def valid_payload(client: httpx.AsyncClient) -> dict[str, object]:
    """Build a canonical payload from persisted catalogue HTTP data."""
    auth = await headers(client)
    movies = (await client.get("/api/movies", headers=auth)).json()["movies"]
    movie = next(item for item in movies if item["title"] == "Paradise")
    theatre = (await client.get("/api/theatres", params={"movie_id": movie["id"]}, headers=auth)).json()["theatres"][0]
    return {"movie_id": movie["id"], "theatre_id": theatre["id"], "seats": ["A1", "A2", "A3"], "payment_method": "CARD"}


async def booking_count() -> int:
    """Return the durable booking row count from PostgreSQL."""
    async with AsyncSessionFactory() as session:
        return int(await session.scalar(select(func.count()).select_from(Booking)) or 0)


@pytest.mark.asyncio
async def test_create_booking_persists_canonical_confirmation_and_requires_bearer(client: httpx.AsyncClient) -> None:
    """Create and re-query one canonical durable booking while rejecting anonymous access."""
    payload = await valid_payload(client)
    assert (await client.post("/api/bookings", json=payload)).status_code == 401
    response = await client.post("/api/bookings", json=payload, headers=await headers(client))
    assert response.status_code == 201
    body = response.json()
    assert body["booking_confirmation_id"].startswith("BMS-")
    assert body["seats"] == ["A1", "A2", "A3"]
    assert body["total_price"] == "450.00"
    assert body["payment_method"] == "CARD"
    async with AsyncSessionFactory() as session:
        row = await session.scalar(select(Booking).where(Booking.confirmation_id == body["booking_confirmation_id"]))
        assert row is not None
        assert row.seats == ["A1", "A2", "A3"]
        assert row.total_price == Decimal("450.00")
        assert row.payment_method.value == "CARD"


@pytest.mark.asyncio
async def test_booking_rejects_bad_client_input_without_extra_rows(client: httpx.AsyncClient) -> None:
    """Reject invalid methods, seat order, mappings, references, and extra fields without inserts."""
    payload = await valid_payload(client)
    auth = await headers(client)
    before = await booking_count()
    invalid_cases = [
        ({**payload, "payment_method": "card"}, 422, "INVALID_PAYMENT_METHOD"),
        ({**payload, "seats": ["A2", "A1", "A3"]}, 422, "INVALID_FIXED_SEATS"),
        ({**payload, "movie_id": str(uuid4())}, 404, "MOVIE_NOT_FOUND"),
        ({**payload, "theatre_id": str(uuid4())}, 404, "THEATRE_NOT_FOUND"),
        ({**payload, "total": 1}, 422, "INVALID_BOOKING_REQUEST"),
    ]
    movies = (await client.get("/api/movies", headers=auth)).json()["movies"]
    og2 = next(item for item in movies if item["title"] == "OG2")
    paradise_theatres = (await client.get("/api/theatres", params={"movie_id": payload["movie_id"]}, headers=auth)).json()["theatres"]
    unmapped_paradise_theatre = paradise_theatres[1]["id"]
    invalid_cases.append(({**payload, "movie_id": og2["id"], "theatre_id": unmapped_paradise_theatre}, 422, "INVALID_THEATRE_FOR_MOVIE"))
    for body, expected_status, expected_code in invalid_cases:
        response = await client.post("/api/bookings", json=body, headers=auth)
        assert response.status_code == expected_status
        assert response.json()["error"]["code"] == expected_code
    assert await booking_count() == before


@pytest.mark.asyncio
async def test_service_validates_each_branch_against_real_database() -> None:
    """Exercise service error branches using real PostgreSQL state without mocked repositories."""
    async with AsyncSessionFactory() as session:
        user = User(mobile_number="9000000001")
        session.add(user)
        await session.commit()
        movie = await session.scalar(select(Movie).where(Movie.title == "Paradise"))
        theatre = await session.scalar(select(Theatre).where(Theatre.name == "Sandhya 70mm"))
        other_theatre = await session.scalar(select(Theatre).where(Theatre.name == "Allu Cinemas"))
        assert user and movie and theatre and other_theatre
        movie_id, theatre_id, other_theatre_id = movie.id, theatre.id, other_theatre.id
        service = BookingService(session)
        with pytest.raises(InvalidPaymentMethodError):
            await service.create_booking(user, BookingCreateRequest(movie_id=movie_id, theatre_id=theatre_id, seats=["A1", "A2", "A3"], payment_method="cash"))
        with pytest.raises(InvalidFixedSeatsError):
            await service.create_booking(user, BookingCreateRequest(movie_id=movie_id, theatre_id=theatre_id, seats=["A3", "A2", "A1"], payment_method="CARD"))
        with pytest.raises(MovieNotFoundForBookingError):
            await service.create_booking(user, BookingCreateRequest(movie_id=uuid4(), theatre_id=theatre_id, seats=["A1", "A2", "A3"], payment_method="CARD"))
        with pytest.raises(TheatreNotFoundError):
            await service.create_booking(user, BookingCreateRequest(movie_id=movie_id, theatre_id=uuid4(), seats=["A1", "A2", "A3"], payment_method="CARD"))
        with pytest.raises(InvalidTheatreForMovieError):
            await service.create_booking(user, BookingCreateRequest(movie_id=movie_id, theatre_id=other_theatre_id, seats=["A1", "A2", "A3"], payment_method="UPI"))
