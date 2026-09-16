"""Coordinate persisted catalogue selection policy."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.catalogue import CatalogueRepository
from app.schemas.catalogue import MovieResponse, TheatreResponse


class MovieNotFoundError(Exception):
    """Signal a requested movie does not exist in the catalogue."""


class CatalogueService:
    """Map catalogue database records into public selection responses."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a service using the request-scoped repository."""
        self._catalogue = CatalogueRepository(session)

    async def list_movies(self) -> list[MovieResponse]:
        """Return ordered movies with their LLD-defined poster paths."""
        movies = await self._catalogue.list_movies()
        return [
            MovieResponse(
                id=movie.id,
                title=movie.title,
                poster_placeholder=f"/assets/posters/{movie.title.lower().replace(' ', '-')}.svg",
            )
            for movie in movies
        ]

    async def list_theatres(self, movie_id: UUID) -> list[TheatreResponse]:
        """Return mapped theatres after ensuring the movie exists."""
        movie = await self._catalogue.get_movie(movie_id)
        if movie is None:
            raise MovieNotFoundError()
        theatres = await self._catalogue.list_theatres_for_movie(movie.id)
        return [TheatreResponse(id=theatre.id, name=theatre.name) for theatre in theatres]
