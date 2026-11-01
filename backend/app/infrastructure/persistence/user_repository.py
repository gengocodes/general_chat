"""PostgreSQL implementation of UserRepositoryPort."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.user_repository_port import UserRepositoryPort
from app.domain.entities.user import AuthenticatedUser, GoogleProfile
from app.domain.errors import PersistenceError
from app.infrastructure.persistence.models import UserModel

logger = logging.getLogger(__name__)

_MAX_UPSERT_ATTEMPTS = 3


def _to_user(model: UserModel) -> AuthenticatedUser:
    return AuthenticatedUser(id=model.id, email=model.email, name=model.name)


class SqlAlchemyUserRepository(UserRepositoryPort):
    """Stores users in PostgreSQL using short, per-operation transactions."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def register_login(self, profile: GoogleProfile) -> AuthenticatedUser:
        # ON CONFLICT only arbitrates google_id. A concurrent first login for the same account
        # can instead trip the email unique index; the retry then resolves via google_id.
        for attempt in range(1, _MAX_UPSERT_ATTEMPTS + 1):
            try:
                return self._upsert_login(profile)
            except IntegrityError as exc:
                if attempt == _MAX_UPSERT_ATTEMPTS:
                    logger.exception("Failed to register Google login")
                    raise PersistenceError("Could not register user.") from exc
            except SQLAlchemyError as exc:
                logger.exception("Failed to register Google login")
                raise PersistenceError("Could not register user.") from exc
        raise AssertionError("unreachable")  # pragma: no cover

    def _upsert_login(self, profile: GoogleProfile) -> AuthenticatedUser:
        statement = (
            insert(UserModel)
            .values(
                id=uuid.uuid4(),
                email=profile.email,
                google_id=profile.google_id,
                name=profile.name,
            )
            .on_conflict_do_update(
                index_elements=[UserModel.google_id],
                set_={
                    "email": profile.email,
                    "name": profile.name,
                    "last_login_at": func.now(),
                },
            )
            .returning(UserModel)
        )
        with self._session_factory.begin() as session:
            return _to_user(session.execute(statement).scalar_one())

    def get_by_id(self, user_id: uuid.UUID) -> AuthenticatedUser | None:
        try:
            with self._session_factory() as session:
                model = session.execute(
                    select(UserModel).where(UserModel.id == user_id)
                ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.exception("Failed to load user")
            raise PersistenceError("Could not load user.") from exc
        return None if model is None else _to_user(model)
