"""Define public catalogue response contracts."""

from uuid import UUID

from pydantic import BaseModel


class MovieResponse(BaseModel):
    """Expose stable movie data for catalogue selection."""

    id: UUID
    title: str
    poster_placeholder: str


class TheatreResponse(BaseModel):
    """Expose a theatre approved for the selected movie."""

    id: UUID
    name: str


class MoviesResponse(BaseModel):
    """Wrap ordered catalogue movies."""

    movies: list[MovieResponse]


class TheatresResponse(BaseModel):
    """Wrap theatres mapped to one movie."""

    theatres: list[TheatreResponse]
