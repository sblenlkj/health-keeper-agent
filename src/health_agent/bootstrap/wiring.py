from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from health_agent.adapters.inbound.api.router import create_api_router
from health_agent.adapters.inbound.scheduler_runtime import SchedulerRuntime
from health_agent.adapters.outbound.persistence.relational.db import create_tables
from health_agent.bootstrap.container import Container


def create_fastapi_app(container: Container) -> FastAPI:
    scheduler_runtime = SchedulerRuntime(
        schedule_runtime_use_cases=container.schedule_runtime_use_cases,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await create_tables(container.engine)

        scheduler_runtime.start()
        await scheduler_runtime.load_active_schedules()

        yield

        await scheduler_runtime.shutdown()

    app = FastAPI(
        title=container.settings.app_name,
        lifespan=lifespan,
    )

    app.include_router(create_api_router(scheduler_runtime))

    return app