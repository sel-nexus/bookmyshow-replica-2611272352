"""Define durable BookMyShow domain entities."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Provide the declarative base shared by all ORM entities."""


class PaymentMethod(str, enum.Enum):
    """Represent accepted booking payment methods."""

    CARD = "CARD"
    UPI = "UPI"


class User(Base):
    """Store an authenticated customer identified by mobile number."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("mobile_number ~ '^[0-9]{10}$'", name="ck_users_mobile_number_ascii_digits"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobile_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Movie(Base):
    """Represent a catalogue movie reserved for later slices."""

    __tablename__ = "movies"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    poster_placeholder: Mapped[str] = mapped_column(String(255), nullable=False)


class Theatre(Base):
    """Represent a cinema theatre reserved for later slices."""

    __tablename__ = "theatres"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)


class MovieTheatre(Base):
    """Map available movies to participating theatres."""

    __tablename__ = "movie_theatres"
    __table_args__ = (
        Index("ix_movie_theatres_movie_id", "movie_id"),
        Index("ix_movie_theatres_theatre_id", "theatre_id"),
    )
    movie_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="RESTRICT"), primary_key=True
    )
    theatre_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("theatres.id", ondelete="RESTRICT"), primary_key=True
    )


class Booking(Base):
    """Represent a future durable booking confirmation."""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("seats = '[\"A1\", \"A2\", \"A3\"]'::jsonb", name="ck_bookings_fixed_seats"),
        CheckConstraint("total_price = 450.00", name="ck_bookings_fixed_total_price"),
        Index("ix_bookings_user_id", "user_id"), Index("ix_bookings_movie_id", "movie_id"),
        Index("ix_bookings_theatre_id", "theatre_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    movie_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False)
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id", ondelete="RESTRICT"), nullable=False)
    seats: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="payment_method"), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    confirmation_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
