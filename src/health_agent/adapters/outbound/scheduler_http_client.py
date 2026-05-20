from __future__ import annotations

from uuid import UUID

import httpx


class HttpSchedulerControlClient:
    """HTTP client for internal scheduler control API."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def track_schedule_cron(self, schedule_cron_id: UUID) -> None:
        await self._post(f"/scheduler/jobs/{schedule_cron_id}/track")

    async def pause_schedule_cron(self, schedule_cron_id: UUID) -> None:
        await self._post(f"/scheduler/jobs/{schedule_cron_id}/pause")

    async def resume_schedule_cron(self, schedule_cron_id: UUID) -> None:
        await self._post(f"/scheduler/jobs/{schedule_cron_id}/resume")

    async def remove_schedule_cron(self, schedule_cron_id: UUID) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.delete(
                f"{self._base_url}/scheduler/jobs/{schedule_cron_id}"
            )

        response.raise_for_status()

    async def _post(self, path: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(f"{self._base_url}{path}")

        response.raise_for_status()