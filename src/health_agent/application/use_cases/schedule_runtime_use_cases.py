from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.application.services.schedule_execution_service import (
    ScheduleExecutionService,
)
from health_agent.domain.entities.schedule_cron import ScheduleCron

import logging

logger = logging.getLogger(__name__)

class ScheduleRuntimeUseCases:
    """Use cases for the scheduler runtime process.

    This class is used by APScheduler/FastAPI scheduler runtime.
    It does not call SchedulerControl because it already runs inside the
    scheduler process.
    """

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        schedule_execution_service: ScheduleExecutionService,
    ) -> None:
        self._uow_factory = uow_factory
        self._schedule_execution_service = schedule_execution_service

    async def get_schedule_cron(self, *, schedule_cron_id: UUID) -> ScheduleCron:
        async with self._uow_factory() as uow:
            schedule = await uow.tracking.get_schedule_cron_by_id(schedule_cron_id)

            if schedule is None:
                raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

            return schedule

    async def list_schedule_crons(
        self,
        *,
        user_profile_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[ScheduleCron]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_schedule_crons(
                user_profile_id=user_profile_id,
                active_only=active_only,
            )

    async def run_schedule_cron(self, *, schedule_cron_id: UUID) -> None:
        logger.info("Running schedule cron %s", schedule_cron_id)

        async with self._uow_factory() as uow:
            await self._schedule_execution_service.execute(
                uow=uow,
                schedule_cron_id=schedule_cron_id,
            )

            await uow.commit()