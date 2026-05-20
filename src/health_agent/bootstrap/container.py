from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

from health_agent.adapters.outbound.telegram_message_sender import TelegramMessageSender
from health_agent.adapters.outbound.persistence.relational.db import (
    create_engine,
    create_session_factory,
)
from health_agent.adapters.outbound.persistence.uow import create_uow_factory
from health_agent.adapters.outbound.scheduler_http_client import HttpSchedulerControlClient
from health_agent.application.ports.message_sender import MessageSender
from health_agent.application.ports.scheduler_control import SchedulerControl
from health_agent.application.services.agent_context_service import AgentContextService
from health_agent.application.services.feedback_service import FeedbackService
from health_agent.application.services.schedule_execution_service import (
    ScheduleExecutionService,
)
from health_agent.application.use_cases.feedback_use_cases import FeedbackUseCases
from health_agent.application.use_cases.observation_use_cases import ObservationUseCases
from health_agent.application.use_cases.schedule_runtime_use_cases import ScheduleRuntimeUseCases
from health_agent.application.use_cases.schedule_management_use_cases import ScheduleManagementUseCases
from health_agent.application.use_cases.tracking_use_cases import TrackingUseCases
from health_agent.application.use_cases.user_profile_use_cases import (
    UserProfileUseCases,
)
from health_agent.core.config import Settings


@dataclass(slots=True)
class Container:
    settings: Settings

    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]

    message_sender: MessageSender
    scheduler_control: SchedulerControl | None

    feedback_service: FeedbackService
    agent_context_service: AgentContextService
    schedule_execution_service: ScheduleExecutionService

    user_profile_use_cases: UserProfileUseCases
    tracking_use_cases: TrackingUseCases
    schedule_runtime_use_cases: ScheduleRuntimeUseCases
    schedule_management_use_cases: ScheduleManagementUseCases
    feedback_use_cases: FeedbackUseCases
    observation_use_cases: ObservationUseCases


def create_container(settings: Settings) -> Container:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    uow_factory = create_uow_factory(session_factory)

    if settings.telegram_bot_token is None:
        message_sender = _NullMessageSender()
    else:
        message_sender = TelegramMessageSender(
            bot_token=settings.telegram_bot_token,
        )

    scheduler_control = HttpSchedulerControlClient(
        base_url=settings.scheduler_control_base_url,
    )

    feedback_service = FeedbackService()

    agent_context_service = AgentContextService()

    schedule_execution_service = ScheduleExecutionService(
        feedback_service=feedback_service,
        message_sender=message_sender,
    )

    schedule_runtime_use_cases = ScheduleRuntimeUseCases(
    uow_factory=uow_factory,
    schedule_execution_service=schedule_execution_service,
)

    schedule_management_use_cases = ScheduleManagementUseCases(
        uow_factory=uow_factory,
        scheduler_control=scheduler_control,
    )

    user_profile_use_cases = UserProfileUseCases(
        uow_factory=uow_factory,
        agent_context_service=agent_context_service,
    )

    tracking_use_cases = TrackingUseCases(
        uow_factory=uow_factory,
    )

    feedback_use_cases = FeedbackUseCases(
        uow_factory=uow_factory,
        feedback_service=feedback_service,
    )

    observation_use_cases = ObservationUseCases(
        uow_factory=uow_factory,
    )

    return Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        message_sender=message_sender,
        scheduler_control=scheduler_control,
        feedback_service=feedback_service,
        agent_context_service=agent_context_service,
        schedule_runtime_use_cases=schedule_runtime_use_cases,
        schedule_management_use_cases=schedule_management_use_cases,
        user_profile_use_cases=user_profile_use_cases,
        tracking_use_cases=tracking_use_cases,
        schedule_execution_service=schedule_execution_service,
        feedback_use_cases=feedback_use_cases,
        observation_use_cases=observation_use_cases,
    )


class _NullMessageSender:
    async def send_message(self, chat_id: int, text: str) -> None:
        print(f"[telegram disabled] chat_id={chat_id}: {text}")