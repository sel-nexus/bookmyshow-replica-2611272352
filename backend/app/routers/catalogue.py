"""Expose authenticated catalogue and mapped theatre endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.entities import User
from app.schemas.catalogue import MoviesResponse, TheatresResponse
from app.services.catalogue import CatalogueService

router = APIRouter(prefix="/api", tags=["catalogue"])


class InvalidMovieIdError(Exception):
    """Signal a theatre query supplied a malformed movie UUID."""


@router.get("/movies", response_model=MoviesResponse, status_code=status.HTTP_200_OK, summary="List selectable movies")
async def list_movies(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MoviesResponse:
    """Return the persisted movie catalogue for an authenticated user."""
    return MoviesResponse(movies=await CatalogueService(session).list_movies())


@router.get("/theatres", response_model=TheatresResponse, status_code=status.HTTP_200_OK, summary="List theatres mapped to a movie")
async def list_theatres(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    movie_id: Annotated[str, Query(min_length=1)],
) -> TheatresResponse:
    """Return only theatres approved for the selected persisted movie."""
    try:
        parsed_movie_id = UUID(movie_id)
    except ValueError as error:
        raise InvalidMovieIdError() from error
    return TheatresResponse(theatres=await CatalogueService(session).list_theatres(parsed_movie_id))
