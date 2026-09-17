"""Create initial users, catalogue mappings, and bookings schema.

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and indexes required by the bounded LLD."""
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                    sa.Column("mobile_number", sa.String(length=10), nullable=False, unique=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                    sa.CheckConstraint("mobile_number ~ '^[0-9]{10}$'", name="ck_users_mobile_number_ascii_digits"))
    op.create_index("ix_users_mobile_number", "users", ["mobile_number"])
    op.create_table("movies", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                    sa.Column("title", sa.String(length=200), nullable=False, unique=True),
                    sa.Column("poster_placeholder", sa.String(length=255), nullable=False))
    op.create_table("theatres", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                    sa.Column("name", sa.String(length=200), nullable=False, unique=True))
    op.create_table("movie_theatres",
                    sa.Column("movie_id", postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("movies.id", ondelete="RESTRICT"), primary_key=True),
                    sa.Column("theatre_id", postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("theatres.id", ondelete="RESTRICT"), primary_key=True))
    op.create_index("ix_movie_theatres_movie_id", "movie_theatres", ["movie_id"])
    op.create_index("ix_movie_theatres_theatre_id", "movie_theatres", ["theatre_id"])
    payment_method = postgresql.ENUM("CARD", "UPI", name="payment_method")
    op.create_table("bookings", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
                    sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
                    sa.Column("movie_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False),
                    sa.Column("theatre_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("theatres.id", ondelete="RESTRICT"), nullable=False),
                    sa.Column("seats", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
                    sa.Column("payment_method", payment_method, nullable=False), sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
                    sa.Column("confirmation_id", sa.String(length=32), nullable=False, unique=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                    sa.CheckConstraint("seats = '[\"A1\", \"A2\", \"A3\"]'::jsonb", name="ck_bookings_fixed_seats"),
                    sa.CheckConstraint("total_price = 450.00", name="ck_bookings_fixed_total_price"))
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_movie_id", "bookings", ["movie_id"])
    op.create_index("ix_bookings_theatre_id", "bookings", ["theatre_id"])


def downgrade() -> None:
    """Drop the initial schema in reverse dependency order."""
    op.drop_table("bookings")
    postgresql.ENUM(name="payment_method").drop(op.get_bind(), checkfirst=True)
    op.drop_table("movie_theatres")
    op.drop_table("theatres")
    op.drop_table("movies")
    op.drop_table("users")
