"""Persist and query booking records through real SQLAlchemy sessions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Booking, Movie, MovieTheatre, Theatre


class BookingRepository:
    """Provide durable booking and catalogue validation queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository operations to a request-scoped session.

        Args:
            session: The open PostgreSQL-backed SQLAlchemy session.
        """
        self._session = session

    async def get_movie(self, movie_id: UUID) -> Movie | None:
        """Fetch a movie by its identity.

        Args:
            movie_id: The requested movie UUID.

        Returns:
            The persisted movie when it exists.
        """
        return await self._session.get(Movie, movie_id)

    async def get_theatre(self, theatre_id: UUID) -> Theatre | None:
        """Fetch a theatre by its identity.

        Args:
            theatre_id: The requested theatre UUID.

        Returns:
            The persisted theatre when it exists.
        """
        return await self._session.get(Theatre, theatre_id)

    async def has_mapping(self, movie_id: UUID, theatre_id: UUID) -> bool:
        """Check whether a movie is authorised for a theatre.

        Args:
            movie_id: The selected movie UUID.
            theatre_id: The selected theatre UUID.

        Returns:
            True only when the mapping exists.
        """
        return (await self._session.scalar(select(MovieTheatre.id).where(
            MovieTheatre.movie_id == movie_id, MovieTheatre.theatre_id == theatre_id
        ))) is not None

    async def confirmation_exists(self, confirmation_id: str) -> bool:
        """Check whether a generated confirmation identifier is already used.

        Args:
            confirmation_id: Candidate public booking confirmation ID.

        Returns:
            True when a durable booking already owns the ID.
        """
        return (await self._session.scalar(select(Booking.id).where(Booking.confirmation_id == confirmation_id))) is not None

    def add(self, booking: Booking) -> None:
        """Stage a booking for the current transaction.

        Args:
            booking: The fully validated booking entity to persist.
        """
        self._session.add(booking)
