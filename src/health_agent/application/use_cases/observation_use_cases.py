from __future__ import annotations

from datetime import datetime
from uuid import UUID

from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.domain.entities.observation import Observation
from health_agent.domain.value_objects.time_window import TimeWindow


class ObservationUseCases:
    """Use cases for important observations."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self._uow_factory = uow_factory

    async def record_observation(
        self,
        *,
        user_profile_id: UUID,
        title: str,
        description: str,
        occurred_at: datetime | None = None,
    ) -> Observation:
        async with self._uow_factory() as uow:
            profile = await uow.users.get_profile_by_id(user_profile_id)
            if profile is None:
                raise ValueError(f"UserProfile with id={user_profile_id} not found.")

            observation = Observation(
                user_profile_id=user_profile_id,
                title=title,
                description=description,
                occurred_at=occurred_at,
            )

            await uow.feedback.add_observation(observation)
            await uow.commit()

            return observation

    async def list_recent_observations(
        self,
        *,
        user_profile_id: UUID,
        limit: int = 20,
    ) -> list[Observation]:
        '''deprecated, left as an artifact for now'''
        async with self._uow_factory() as uow:
            return await uow.feedback.list_recent_observations(
                user_profile_id,
                limit=limit,
            )

    async def list_observations_by_window(
        self,
        *,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[Observation]:
        async with self._uow_factory() as uow:
            return await uow.feedback.list_observations_by_window(
                user_profile_id,
                window,
            )