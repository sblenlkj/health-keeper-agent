from __future__ import annotations

from typing import Protocol
from uuid import UUID

from health_agent.domain.entities.feedback_item import FeedbackItem
from health_agent.domain.entities.observation import Observation
from health_agent.domain.value_objects.time_window import TimeWindow


class FeedbackRepository(Protocol):
    """Repository for collected user feedback and important observations."""

    async def add_feedback_item(self, item: FeedbackItem) -> None:
        ...

    async def get_feedback_item_by_id(
        self,
        feedback_item_id: UUID,
    ) -> FeedbackItem | None:
        ...

    async def list_pending_feedback_items(
        self,
        user_profile_id: UUID,
    ) -> list[FeedbackItem]:
        ...

    async def list_feedback_items_by_window(
        self,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[FeedbackItem]:
        ...

    async def save_feedback_item(self, item: FeedbackItem) -> None:
        ...

    async def add_observation(self, observation: Observation) -> None:
        ...

    async def list_recent_observations(
        self,
        user_profile_id: UUID,
        *,
        limit: int = 20,
    ) -> list[Observation]:
        ...

    async def list_observations_by_window(
        self,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[Observation]:
        ...