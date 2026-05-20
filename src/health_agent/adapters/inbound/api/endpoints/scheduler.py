from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from health_agent.adapters.inbound.scheduler_runtime import SchedulerRuntime


def create_scheduler_router(scheduler_runtime: SchedulerRuntime) -> APIRouter:
    router = APIRouter(prefix="/scheduler", tags=["scheduler"])

    @router.post(
        "/jobs/{schedule_cron_id}/track",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def track_schedule_cron(schedule_cron_id: UUID) -> None:
        await scheduler_runtime.track_schedule_cron(schedule_cron_id)

    @router.post(
        "/jobs/{schedule_cron_id}/pause",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def pause_schedule_cron(schedule_cron_id: UUID) -> None:
        await scheduler_runtime.pause_schedule_cron(schedule_cron_id)

    @router.post(
        "/jobs/{schedule_cron_id}/resume",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def resume_schedule_cron(schedule_cron_id: UUID) -> None:
        await scheduler_runtime.resume_schedule_cron(schedule_cron_id)

    @router.delete(
        "/jobs/{schedule_cron_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def remove_schedule_cron(schedule_cron_id: UUID) -> None:
        await scheduler_runtime.remove_schedule_cron(schedule_cron_id)

    return router