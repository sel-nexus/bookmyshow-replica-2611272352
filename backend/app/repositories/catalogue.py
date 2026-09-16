"""Query persisted catalogue records with SQLAlchemy."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Movie, MovieTheatre, Theatre


class CatalogueRepository:
    """Provide database-backed movie and theatre read queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository queries to a request-scoped session."""
        self._session = session

    async def list_movies(self) -> list[Movie]:
        """Return all movies in ascending title order."""
        result = await self._session.scalars(select(Movie).order_by(Movie.title))
        return list(result)

    async def get_movie(self, movie_id: UUID) -> Movie | None:
        """Return a movie by its persisted identifier when present."""
        return await self._session.get(Movie, movie_id)

    async def list_theatres_for_movie(self, movie_id: UUID) -> list[Theatre]:
        """Return only theatres explicitly mapped to a movie by name."""
        statement = (
            select(Theatre)
            .join(MovieTheatre, MovieTheatre.theatre_id == Theatre.id)
            .where(MovieTheatre.movie_id == movie_id)
            .order_by(Theatre.name)
        )
        result = await self._session.scalars(statement)
        return list(result)
