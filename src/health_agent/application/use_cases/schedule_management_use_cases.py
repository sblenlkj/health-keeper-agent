from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.scheduler_control import SchedulerControl
from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.domain.entities.schedule_cron import ScheduleCron

import logging

logger = logging.getLogger(__name__)

class ScheduleManagementUseCases:
    """Use cases for managing schedule crons from MCP/API side.

    This class is used by inbound adapters that create or modify schedules.
    It saves changes to the database and notifies the external scheduler runtime.
    """

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        scheduler_control: SchedulerControl,
    ) -> None:
        self._uow_factory = uow_factory
        self._scheduler_control = scheduler_control

    async def create_schedule_cron(
        self,
        *,
        user_profile_id: UUID,
        title: str,
        cron: str,
        description: str | None = None,
    ) -> ScheduleCron:
        async with self._uow_factory() as uow:
            profile = await uow.users.get_profile_by_id(user_profile_id)
            if profile is None:
                raise ValueError(f"UserProfile with id={user_profile_id} not found.")

            schedule = ScheduleCron(
                user_profile_id=user_profile_id,
                title=title,
                description=description,
                cron=cron,
            )

            await uow.tracking.add_schedule_cron(schedule)
            await uow.commit()

        logger.info(
            "Created schedule cron %s for user_profile_id=%s",
            schedule.id,
            user_profile_id,
        )

        logger.info("Registering schedule cron %s in scheduler runtime", schedule.id)
        await self._scheduler_control.track_schedule_cron(schedule.id)

        return schedule

    async def list_schedule_crons(
        self,
        *,
        user_profile_id: UUID,
        active_only: bool = True,
    ) -> list[ScheduleCron]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_schedule_crons(
                user_profile_id=user_profile_id,
                active_only=active_only,
            )

    async def pause_schedule_cron(self, *, schedule_cron_id: UUID) -> ScheduleCron:
        async with self._uow_factory() as uow:
            schedule = await uow.tracking.get_schedule_cron_by_id(schedule_cron_id)
            if schedule is None:
                raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

            schedule.is_active = False

            await uow.tracking.save_schedule_cron(schedule)
            await uow.commit()

        await self._scheduler_control.pause_schedule_cron(schedule_cron_id)

        return schedule

    async def resume_schedule_cron(self, *, schedule_cron_id: UUID) -> ScheduleCron:
        async with self._uow_factory() as uow:
            schedule = await uow.tracking.get_schedule_cron_by_id(schedule_cron_id)
            if schedule is None:
                raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

            schedule.is_active = True

            await uow.tracking.save_schedule_cron(schedule)
            await uow.commit()

        await self._scheduler_control.resume_schedule_cron(schedule_cron_id)

        return schedule