from __future__ import annotations

from typing import Protocol
from uuid import UUID


class SchedulerControl(Protocol):
    """Outbound port for controlling scheduler runtime."""

    async def track_schedule_cron(self, schedule_cron_id: UUID) -> None:
        ...

    async def pause_schedule_cron(self, schedule_cron_id: UUID) -> None:
        ...

    async def resume_schedule_cron(self, schedule_cron_id: UUID) -> None:
        ...

    async def remove_schedule_cron(self, schedule_cron_id: UUID) -> None:
        ...