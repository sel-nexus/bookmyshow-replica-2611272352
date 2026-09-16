"""Verify the auth, catalogue, and booking journey through real HTTP and PostgreSQL."""

from test_bookings import client, postgres_schema, headers

import pytest
from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.entities import Booking


@pytest.mark.asyncio
async def test_auth_movies_theatres_booking_chain_persists_durable_confirmation(client) -> None:
    """Chain four HTTP surfaces and re-query the final booking from PostgreSQL."""
    auth = await headers(client)
    movies_response = await client.get("/api/movies", headers=auth)
    movie = next(item for item in movies_response.json()["movies"] if item["title"] == "Paradise")
    theatres_response = await client.get("/api/theatres", params={"movie_id": movie["id"]}, headers=auth)
    theatre = theatres_response.json()["theatres"][0]
    booking_response = await client.post("/api/bookings", headers=auth, json={"movie_id": movie["id"], "theatre_id": theatre["id"], "seats": ["A1", "A2", "A3"], "payment_method": "UPI"})
    assert booking_response.status_code == 201
    confirmation = booking_response.json()
    assert confirmation["movie"]["title"] == "Paradise"
    assert confirmation["theatre"]["name"] == theatre["name"]
    async with AsyncSessionFactory() as session:
        row = await session.scalar(select(Booking).where(Booking.confirmation_id == confirmation["booking_confirmation_id"]))
        assert row is not None and row.payment_method.value == "UPI"


@pytest.mark.asyncio
async def test_auth_catalogue_invalid_mapping_chain_returns_domain_error(client) -> None:
    """Chain auth and catalogue data into a cross-feature mapping error without an insert."""
    auth = await headers(client)
    movies = (await client.get("/api/movies", headers=auth)).json()["movies"]
    paradise = next(item for item in movies if item["title"] == "Paradise")
    og2 = next(item for item in movies if item["title"] == "OG2")
    unmapped_paradise_theatre = (await client.get("/api/theatres", params={"movie_id": paradise["id"]}, headers=auth)).json()["theatres"][1]
    response = await client.post("/api/bookings", headers=auth, json={"movie_id": og2["id"], "theatre_id": unmapped_paradise_theatre["id"], "seats": ["A1", "A2", "A3"], "payment_method": "CARD"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_THEATRE_FOR_MOVIE"
