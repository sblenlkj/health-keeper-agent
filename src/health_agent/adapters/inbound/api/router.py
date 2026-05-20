from __future__ import annotations

from fastapi import APIRouter

from health_agent.adapters.inbound.api.endpoints.scheduler import (
    create_scheduler_router,
)
from health_agent.adapters.inbound.scheduler_runtime import SchedulerRuntime


def create_api_router(scheduler_runtime: SchedulerRuntime) -> APIRouter:
    router = APIRouter()

    router.include_router(create_scheduler_router(scheduler_runtime))

    return router