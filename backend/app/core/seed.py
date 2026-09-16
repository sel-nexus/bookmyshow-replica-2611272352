"""Idempotently seed the bounded movie and theatre catalogue."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Movie, MovieTheatre, Theatre

MOVIE_TITLES = ("Paradise", "Bloody Romeo", "OG2")
THEATRE_NAMES = ("Sandhya 70mm", "Sudharsham 70mm", "Allu Cinemas")
APPROVED_MAPPINGS = {
    "Paradise": ("Sandhya 70mm", "Sudharsham 70mm"),
    "Bloody Romeo": ("Allu Cinemas",),
    "OG2": ("Sandhya 70mm",),
}


async def seed_database(session: AsyncSession) -> None:
    """Insert required catalogue records and mappings only when absent."""
    movies_by_title: dict[str, Movie] = {}
    theatres_by_name: dict[str, Theatre] = {}

    for title in MOVIE_TITLES:
        movie = await session.scalar(select(Movie).where(Movie.title == title))
        if movie is None:
            movie = Movie(title=title)
            session.add(movie)
            await session.flush()
        movies_by_title[title] = movie

    for name in THEATRE_NAMES:
        theatre = await session.scalar(select(Theatre).where(Theatre.name == name))
        if theatre is None:
            theatre = Theatre(name=name)
            session.add(theatre)
            await session.flush()
        theatres_by_name[name] = theatre

    for title, theatre_names in APPROVED_MAPPINGS.items():
        for theatre_name in theatre_names:
            mapping = await session.scalar(
                select(MovieTheatre).where(
                    MovieTheatre.movie_id == movies_by_title[title].id,
                    MovieTheatre.theatre_id == theatres_by_name[theatre_name].id,
                )
            )
            if mapping is None:
                session.add(MovieTheatre(movie_id=movies_by_title[title].id, theatre_id=theatres_by_name[theatre_name].id))
    await session.commit()
