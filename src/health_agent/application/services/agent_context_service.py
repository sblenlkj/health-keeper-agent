from __future__ import annotations

from uuid import UUID

from health_agent.application.dto.agent_context import (
    AgentContext,
    TrackingTargetContext,
)
from health_agent.application.ports.unit_of_work import UnitOfWork


class AgentContextService:
    """Builds compact LLM-facing context for the agent.

    This service does not own transaction boundaries.
    The caller must pass an already opened UnitOfWork.

    The context is intentionally small:
    - user-facing profile data;
    - active tracking targets.

    The agent should use tools to fetch questions, reminders, feedback,
    observations, and other operational data when needed.
    """

    async def build_by_telegram_user_id(
        self,
        *,
        uow: UnitOfWork,
        telegram_user_id: int,
    ) -> AgentContext:
        user = await uow.users.get_user_by_telegram_id(telegram_user_id)
        if user is None:
            raise ValueError(
                f"User with telegram_user_id={telegram_user_id} not found."
            )

        profile = await uow.users.get_profile_by_user_id(user.id)
        if profile is None:
            raise ValueError(f"UserProfile for user_id={user.id} not found.")

        targets = await uow.tracking.list_tracking_targets(
            profile.id,
            active_only=True,
        )

        return AgentContext(
            display_name=user.display_name,
            language=profile.language,
            communication_style=profile.communication_style,
            general_notes=profile.general_notes,
            tracking_targets=[
                TrackingTargetContext(
                    title=target.title,
                    code=str(target.code),
                    description=target.description,
                )
                for target in targets
            ],
        )

    async def build_by_user_profile_id(
        self,
        *,
        uow: UnitOfWork,
        user_profile_id: UUID,
    ) -> AgentContext:
        profile = await uow.users.get_profile_by_id(user_profile_id)
        if profile is None:
            raise ValueError(f"UserProfile with id={user_profile_id} not found.")

        user = await uow.users.get_user_by_id(profile.user_id)
        targets = await uow.tracking.list_tracking_targets(
            profile.id,
            active_only=True,
        )

        return AgentContext(
            display_name=user.display_name if user else None,
            language=profile.language,
            communication_style=profile.communication_style,
            general_notes=profile.general_notes,
            tracking_targets=[
                TrackingTargetContext(
                    title=target.title,
                    code=str(target.code),
                    description=target.description,
                )
                for target in targets
            ],
        )