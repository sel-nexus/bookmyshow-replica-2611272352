"""Apply atomic server-authoritative booking confirmation policy."""

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Booking, PaymentMethod, User
from app.repositories.bookings import BookingRepository
from app.schemas.bookings import BookingConfirmationResponse, BookingCreateRequest, BookingMovieResponse, BookingTheatreResponse

FIXED_SEATS = ["A1", "A2", "A3"]
FIXED_TOTAL_PRICE = Decimal("450.00")


class InvalidPaymentMethodError(Exception):
    """Signal an unsupported payment method."""


class InvalidFixedSeatsError(Exception):
    """Signal a non-canonical seat list or ordering."""


class MovieNotFoundForBookingError(Exception):
    """Signal a missing booking movie."""


class TheatreNotFoundError(Exception):
    """Signal a missing booking theatre."""


class InvalidTheatreForMovieError(Exception):
    """Signal a theatre not mapped to the selected movie."""


class BookingNotFoundError(Exception):
    """Signal a missing or non-owned booking confirmation."""


class BookingService:
    """Create durable confirmations after every authoritative validation passes."""

    def __init__(self, session: AsyncSession) -> None:
        """Create the service with its request-scoped database session.

        Args:
            session: The PostgreSQL session whose transaction this service owns.
        """
        self._session = session
        self._bookings = BookingRepository(session)

    async def create_booking(self, user: User, request: BookingCreateRequest) -> BookingConfirmationResponse:
        """Validate and commit one booking in a single transaction.

        Args:
            user: The authenticated booking customer.
            request: Strict selection and payment-method input.

        Returns:
            The persisted server-authoritative booking confirmation.

        Raises:
            InvalidPaymentMethodError: If the submitted method is unsupported.
            InvalidFixedSeatsError: If the exact fixed seats are not supplied in order.
            MovieNotFoundForBookingError: If the selected movie does not exist.
            TheatreNotFoundError: If the selected theatre does not exist.
            InvalidTheatreForMovieError: If the valid references are not mapped.
        """
        user_id = inspect(user).identity[0]
        if self._session.in_transaction():
            await self._session.rollback()
        async with self._session.begin():
            try:
                payment_method = PaymentMethod(request.payment_method)
            except ValueError as error:
                raise InvalidPaymentMethodError() from error
            if request.seats != FIXED_SEATS:
                raise InvalidFixedSeatsError()
            movie = await self._bookings.get_movie(request.movie_id)
            if movie is None:
                raise MovieNotFoundForBookingError()
            theatre = await self._bookings.get_theatre(request.theatre_id)
            if theatre is None:
                raise TheatreNotFoundError()
            if not await self._bookings.has_mapping(movie.id, theatre.id):
                raise InvalidTheatreForMovieError()
            confirmation_id = await self._new_confirmation_id()
            booking = Booking(
                user_id=user_id,
                movie_id=movie.id,
                theatre_id=theatre.id,
                seats=FIXED_SEATS,
                total_price=FIXED_TOTAL_PRICE,
                payment_method=payment_method,
                confirmation_id=confirmation_id,
                created_at=datetime.now(UTC),
            )
            self._bookings.add(booking)
            await self._session.flush()
            response = BookingConfirmationResponse(
                booking_confirmation_id=booking.confirmation_id,
                movie=BookingMovieResponse(id=movie.id, title=movie.title),
                theatre=BookingTheatreResponse(id=theatre.id, name=theatre.name),
                seats=list(booking.seats),
                total_price=booking.total_price,
                payment_method=booking.payment_method.value,
                booked_at=booking.created_at,
            )
        return response

    async def get_booking(self, user: User, confirmation_id: str) -> BookingConfirmationResponse:
        """Read one durable confirmation owned by the authenticated customer.

        Args:
            user: The bearer-authenticated customer.
            confirmation_id: The public confirmation identifier from the route.

        Returns:
            The persisted confirmation details.

        Raises:
            BookingNotFoundError: If no booking with this identifier belongs to the user.
        """
        user_id = inspect(user).identity[0]
        result = await self._bookings.get_for_user(confirmation_id, user_id)
        if result is None:
            raise BookingNotFoundError()
        booking, movie, theatre = result
        return BookingConfirmationResponse(
            booking_confirmation_id=booking.confirmation_id,
            movie=BookingMovieResponse(id=movie.id, title=movie.title),
            theatre=BookingTheatreResponse(id=theatre.id, name=theatre.name),
            seats=list(booking.seats),
            total_price=booking.total_price,
            payment_method=booking.payment_method.value,
            booked_at=booking.created_at,
        )

    async def _new_confirmation_id(self) -> str:
        """Generate an unused public confirmation identifier.

        Returns:
            A random, date-prefixed identifier protected by a database uniqueness constraint.
        """
        date_prefix = datetime.now(UTC).strftime("%Y%m%d")
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(10):
            candidate = f"BMS-{date_prefix}-" + "".join(secrets.choice(alphabet) for _ in range(6))
            if not await self._bookings.confirmation_exists(candidate):
                return candidate
        raise RuntimeError("Unable to allocate a unique booking confirmation ID")
