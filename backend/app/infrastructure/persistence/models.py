"""SQLAlchemy table models. Schema changes must ship with an Alembic revision."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Declarative base shared by all persistence models."""


class UserModel(Base):  # pylint: disable=too-few-public-methods
    """A signed-in user. Google is the only sign-in method."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    google_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GuestUsageModel(Base):  # pylint: disable=too-few-public-methods
    """Free chat messages consumed by an anonymous guest."""

    __tablename__ = "guest_usage"
    __table_args__ = (
        CheckConstraint("message_count >= 0", name="ck_guest_usage_count_non_negative"),
    )

    guest_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
