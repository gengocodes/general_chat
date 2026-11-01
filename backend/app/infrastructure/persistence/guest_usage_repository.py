"""PostgreSQL implementation of GuestUsagePort."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.guest_usage_port import GuestUsagePort
from app.domain.errors import PersistenceError
from app.infrastructure.persistence.models import GuestUsageModel

logger = logging.getLogger(__name__)


class SqlAlchemyGuestUsageRepository(GuestUsagePort):
    """Tracks guest free-message usage with an atomic conditional upsert."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def used_count(self, guest_id: uuid.UUID) -> int:
        try:
            with self._session_factory() as session:
                count = session.execute(
                    select(GuestUsageModel.message_count).where(
                        GuestUsageModel.guest_id == guest_id
                    )
                ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.exception("Failed to read guest usage")
            raise PersistenceError("Could not read guest usage.") from exc
        return 0 if count is None else count

    def try_consume(self, guest_id: uuid.UUID, limit: int) -> bool:
        # `limit` is at least 1, so the first insert (count=1) never exceeds it.
        statement = (
            insert(GuestUsageModel)
            .values(guest_id=guest_id, message_count=1)
            .on_conflict_do_update(
                index_elements=[GuestUsageModel.guest_id],
                set_={
                    "message_count": GuestUsageModel.message_count + 1,
                    "updated_at": func.now(),
                },
                where=GuestUsageModel.message_count < limit,
            )
            .returning(GuestUsageModel.message_count)
        )
        try:
            with self._session_factory.begin() as session:
                return session.execute(statement).scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            logger.exception("Failed to consume guest message")
            raise PersistenceError("Could not record guest usage.") from exc
