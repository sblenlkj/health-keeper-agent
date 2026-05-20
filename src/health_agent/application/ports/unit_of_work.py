from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from health_agent.application.ports.feedback_repository import FeedbackRepository
from health_agent.application.ports.tracking_repository import TrackingRepository
from health_agent.application.ports.user_profile_repository import (
    UserProfileRepository,
)


class UnitOfWork(Protocol):
    """Application unit of work."""

    @property
    def users(self) -> UserProfileRepository:
        ...

    @property
    def tracking(self) -> TrackingRepository:
        ...

    @property
    def feedback(self) -> FeedbackRepository:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


UnitOfWorkFactory = Callable[[], UnitOfWork]