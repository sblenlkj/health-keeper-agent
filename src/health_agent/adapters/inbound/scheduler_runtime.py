from __future__ import annotations

from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from health_agent.application.use_cases.schedule_runtime_use_cases import ScheduleRuntimeUseCases


class SchedulerRuntime:
    """APScheduler runtime adapter.

    This class owns APScheduler and knows how to register/pause jobs.
    Business logic is delegated to ScheduleUseCases.
    """

    def __init__(self, schedule_runtime_use_cases: ScheduleRuntimeUseCases) -> None:
        self._schedule_runtime_use_cases = schedule_runtime_use_cases
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def track_schedule_cron(self, schedule_cron_id: UUID) -> None:
        schedule = await self._schedule_runtime_use_cases.get_schedule_cron(
            schedule_cron_id=schedule_cron_id,
        )

        if not schedule.is_active:
            return

        job_id = self._build_job_id(schedule.id)

        if self._scheduler.get_job(job_id) is not None:
            self._scheduler.remove_job(job_id)

        self._scheduler.add_job(
            self._run_schedule_cron,
            trigger=CronTrigger.from_crontab(schedule.cron, timezone="UTC"),
            id=job_id,
            replace_existing=True,
            kwargs={"schedule_cron_id": schedule.id},
        )

    async def pause_schedule_cron(self, schedule_cron_id: UUID) -> None:
        job_id = self._build_job_id(schedule_cron_id)
        job = self._scheduler.get_job(job_id)

        if job is not None:
            job.pause()

    async def resume_schedule_cron(self, schedule_cron_id: UUID) -> None:
        job_id = self._build_job_id(schedule_cron_id)
        job = self._scheduler.get_job(job_id)

        if job is not None:
            job.resume()
        else:
            await self.track_schedule_cron(schedule_cron_id)

    async def remove_schedule_cron(self, schedule_cron_id: UUID) -> None:
        job_id = self._build_job_id(schedule_cron_id)

        if self._scheduler.get_job(job_id) is not None:
            self._scheduler.remove_job(job_id)

    async def load_active_schedules(self) -> None:
        schedules = await self._schedule_runtime_use_cases.list_schedule_crons()

        for schedule in schedules:
            await self.track_schedule_cron(schedule.id)

    async def _run_schedule_cron(self, schedule_cron_id: UUID) -> None:
        await self._schedule_runtime_use_cases.run_schedule_cron(
            schedule_cron_id=schedule_cron_id,
        )

    @staticmethod
    def _build_job_id(schedule_cron_id: UUID) -> str:
        return f"schedule-cron:{schedule_cron_id}"