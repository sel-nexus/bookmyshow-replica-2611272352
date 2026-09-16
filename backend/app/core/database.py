"""Provision PostgreSQL databases and expose async SQLAlchemy sessions."""

import re
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()


def application_database_url() -> str:
    """Compose the application URL by replacing the maintenance database name.

    Returns:
        A SQLAlchemy URL string targeting the configured application database.
    """
    base_url = make_url(settings.database_url)
    return URL.create(base_url.drivername, base_url.username, base_url.password, base_url.host,
                      base_url.port, settings.db_name, base_url.query).render_as_string(hide_password=False)


engine = create_async_engine(application_database_url(), pool_size=5, max_overflow=5, pool_pre_ping=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def ensure_database_exists() -> None:
    """Create the configured PostgreSQL database when it is absent.

    Raises:
        DBAPIError: If PostgreSQL rejects a non-concurrent provisioning operation.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]+", settings.db_name):
        raise ValueError("DB_NAME must contain only letters, numbers, and underscores")
    maintenance_engine = create_async_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    try:
        async with maintenance_engine.connect() as connection:
            exists = await connection.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"),
                                             {"name": settings.db_name})
            if not exists:
                try:
                    await connection.execute(text(f'CREATE DATABASE "{settings.db_name}"'))
                except DBAPIError as error:
                    if getattr(error.orig, "sqlstate", None) != "42P04":
                        raise
    finally:
        await maintenance_engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a database session and guarantee its closure.

    Yields:
        An async session bound to the configured application database.
    """
    async with AsyncSessionFactory() as session:
        yield session
