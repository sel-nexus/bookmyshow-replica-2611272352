"""Persist and retrieve users through PostgreSQL."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User


class UserRepository:
    """Encapsulate durable user queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the request-scoped database session.

        Args:
            session: The active async SQLAlchemy session.
        """
        self._session = session

    async def get_by_mobile_number(self, mobile_number: str) -> User | None:
        """Find a user by their canonical mobile number.

        Args:
            mobile_number: The validated ten-digit mobile number.

        Returns:
            The matching user when present, otherwise None.
        """
        result = await self._session.execute(select(User).where(User.mobile_number == mobile_number))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: object) -> User | None:
        """Find a user by their UUID primary key.

        Args:
            user_id: The JWT subject UUID to resolve.

        Returns:
            The matching persistent user when present, otherwise None.
        """
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, mobile_number: str) -> User:
        """Retrieve a user or transactionally persist a new one.

        Args:
            mobile_number: The validated ten-digit mobile number.

        Returns:
            The existing or newly persisted user.
        """
        existing = await self.get_by_mobile_number(mobile_number)
        if existing is not None:
            return existing
        user = User(mobile_number=mobile_number)
        self._session.add(user)
        await self._session.flush()
        return user
