"""Exercise durable booking confirmation behavior against real PostgreSQL."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

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
from sqlalchemy import delete, func, select
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

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


def expired_authorization_header() -> dict[str, str]:
    """Build a validly signed bearer token that has already expired."""
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": str(uuid4()), "iss": "bookmyshow-api", "aud": "bookmyshow-web",
         "iat": int((now - timedelta(hours=2)).timestamp()), "exp": int((now - timedelta(hours=1)).timestamp())},
        os.environ["JWT_SECRET"], algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("authorization", [None, {"Authorization": "Bearer not-a-jwt"}, expired_authorization_header()])
async def test_booking_rejects_absent_malformed_and_expired_bearers_without_mutation(
    client: httpx.AsyncClient, authorization: dict[str, str] | None
) -> None:
    """Reject each bearer failure before creating a durable booking row."""
    payload = await valid_payload(client)
    before = await booking_count()
    response = await client.post("/api/bookings", json=payload, headers=authorization)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
    assert "traceback" not in response.text.lower()
    assert await booking_count() == before


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
async def test_get_booking_reads_persisted_confirmation_only_for_its_authenticated_owner(client: httpx.AsyncClient) -> None:
    """Read a created confirmation through the HTTP API without exposing another user's booking."""
    owner_headers = await headers(client)
    created = await client.post("/api/bookings", json=await valid_payload(client), headers=owner_headers)
    assert created.status_code == 201
    confirmation_id = created.json()["booking_confirmation_id"]

    read = await client.get(f"/api/bookings/{confirmation_id}", headers=owner_headers)
    assert read.status_code == 200
    assert read.json() == created.json()

    other_token = await client.post("/api/auth/verify", json={"mobile_number": "9000000009", "otp": "1234"})
    other_headers = {"Authorization": f"Bearer {other_token.json()['access_token']}"}
    forbidden = await client.get(f"/api/bookings/{confirmation_id}", headers=other_headers)
    missing = await client.get("/api/bookings/BMS-20260916-MISSING", headers=owner_headers)
    anonymous = await client.get(f"/api/bookings/{confirmation_id}")
    assert forbidden.status_code == 404
    assert forbidden.json()["error"]["code"] == "BOOKING_NOT_FOUND"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "BOOKING_NOT_FOUND"
    assert anonymous.status_code == 401
    assert anonymous.json()["error"]["code"] == "AUTH_REQUIRED"
    async with AsyncSessionFactory() as session:
        await session.execute(delete(Booking).where(Booking.confirmation_id == confirmation_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_payload", [
    {},
    {"movie_id": None, "theatre_id": None, "seats": None, "payment_method": None},
    {"movie_id": 1, "theatre_id": 2, "seats": "A1", "payment_method": 3},
    {"seats": [], "payment_method": "CARD"},
    {"seats": ["A1"] * 1000, "payment_method": "CARD"},
    {"seats": ["A1", "A2", "A3"], "payment_method": "CARD", "unexpected": "'; DROP TABLE bookings; --"},
])
async def test_booking_request_shape_rejections_do_not_mutate(
    client: httpx.AsyncClient, invalid_payload: dict[str, object]
) -> None:
    """Reject absent, null, invalid-type, boundary, oversized, and hostile request bodies."""
    before = await booking_count()
    response = await client.post("/api/bookings", json=invalid_payload, headers=await headers(client))
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"INVALID_BOOKING_REQUEST", "INVALID_FIXED_SEATS"}
    assert "traceback" not in response.text.lower()
    assert await booking_count() == before


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
async def test_confirmation_id_retries_after_collision_against_real_postgresql() -> None:
    """Skip a persisted collision and return the next distinct random candidate."""
    await engine.dispose()
    async with AsyncSessionFactory() as session:
        user = User(mobile_number="9000000003")
        session.add(user)
        movie = await session.scalar(select(Movie).where(Movie.title == "Paradise"))
        theatre = await session.scalar(select(Theatre).where(Theatre.name == "Sandhya 70mm"))
        assert movie is not None and theatre is not None
        date_prefix = datetime.now(UTC).strftime("%Y%m%d")
        collision_id = f"BMS-{date_prefix}-AAAAAA"
        session.add(Booking(
            user_id=user.id, movie_id=movie.id, theatre_id=theatre.id,
            seats=["A1", "A2", "A3"], payment_method="CARD", total_price=Decimal("450.00"),
            confirmation_id=collision_id,
        ))
        await session.commit()
        service = BookingService(session)
        with patch("app.services.bookings.secrets.choice", side_effect=[*"AAAAAA", *"BBBBBB"]):
            confirmation_id = await service._new_confirmation_id()
    assert confirmation_id == f"BMS-{date_prefix}-BBBBBB"
    await engine.dispose()


@pytest.mark.asyncio
async def test_confirmation_id_raises_after_all_candidates_collide_against_real_postgresql() -> None:
    """Raise the controlled exhaustion error when all generated candidates are persisted."""
    await engine.dispose()
    async with AsyncSessionFactory() as session:
        user = User(mobile_number="9000000004")
        session.add(user)
        movie = await session.scalar(select(Movie).where(Movie.title == "Paradise"))
        theatre = await session.scalar(select(Theatre).where(Theatre.name == "Sandhya 70mm"))
        assert movie is not None and theatre is not None
        date_prefix = datetime.now(UTC).strftime("%Y%m%d")
        collision_id = f"BMS-{date_prefix}-CCCCCC"
        session.add(Booking(
            user_id=user.id, movie_id=movie.id, theatre_id=theatre.id,
            seats=["A1", "A2", "A3"], payment_method="CARD", total_price=Decimal("450.00"),
            confirmation_id=collision_id,
        ))
        await session.commit()
        service = BookingService(session)
        with patch("app.services.bookings.secrets.choice", side_effect=["C"] * 60):
            with pytest.raises(RuntimeError, match="Unable to allocate a unique booking confirmation ID"):
                await service._new_confirmation_id()
    await engine.dispose()


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


@pytest.mark.asyncio
async def test_database_enforces_unique_mobile_foreign_keys_and_fixed_jsonb_seats() -> None:
    """Verify real PostgreSQL integrity constraints declared by the aligned LLD schema."""
    await engine.dispose()
    async with AsyncSessionFactory() as session:
        user = User(mobile_number="9000000002")
        session.add(user)
        await session.commit()
        user_id = user.id
        session.add(User(mobile_number="9000000002"))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

        movie = await session.scalar(select(Movie).where(Movie.title == "Paradise"))
        theatre = await session.scalar(select(Theatre).where(Theatre.name == "Sandhya 70mm"))
        assert movie is not None and theatre is not None
        movie_id, theatre_id = movie.id, theatre.id
        session.add(Booking(
            user_id=uuid4(), movie_id=movie_id, theatre_id=theatre_id,
            seats=["A1", "A2", "A3"], payment_method="CARD", total_price=Decimal("450.00"),
            confirmation_id="BMS-FOREIGN-KEY-TEST",
        ))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

        session.add(Booking(
            user_id=user_id, movie_id=movie_id, theatre_id=theatre_id,
            seats=["A3", "A2", "A1"], payment_method="CARD", total_price=Decimal("450.00"),
            confirmation_id="BMS-JSONB-CHECK-TEST",
        ))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
    await engine.dispose()
