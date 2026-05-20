from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from health_agent.adapters.outbound.persistence.relational.repositories import (
    SqlAlchemyFeedbackRepository,
    SqlAlchemyTrackingRepository,
    SqlAlchemyUserProfileRepository,
)
from health_agent.application.ports.feedback_repository import FeedbackRepository
from health_agent.application.ports.tracking_repository import TrackingRepository
from health_agent.application.ports.user_profile_repository import (
    UserProfileRepository,
)

from health_agent.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory

def create_uow_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UnitOfWorkFactory:
    def factory() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return factory


class SqlAlchemyUnitOfWork:
    """SQLAlchemy implementation of UnitOfWork."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

        self._users: UserProfileRepository | None = None
        self._tracking: TrackingRepository | None = None
        self._feedback: FeedbackRepository | None = None

    @property
    def users(self) -> UserProfileRepository:
        if self._users is None:
            raise RuntimeError("UnitOfWork is not initialized.")
        return self._users

    @property
    def tracking(self) -> TrackingRepository:
        if self._tracking is None:
            raise RuntimeError("UnitOfWork is not initialized.")
        return self._tracking

    @property
    def feedback(self) -> FeedbackRepository:
        if self._feedback is None:
            raise RuntimeError("UnitOfWork is not initialized.")
        return self._feedback

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()

        self._users = SqlAlchemyUserProfileRepository(self._session)
        self._tracking = SqlAlchemyTrackingRepository(self._session)
        self._feedback = SqlAlchemyFeedbackRepository(self._session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        if exc_type is not None:
            await self.rollback()

        await self._session.close()

        self._session = None
        self._users = None
        self._tracking = None
        self._feedback = None

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork session is not initialized.")

        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork session is not initialized.")

        await self._session.rollback()
