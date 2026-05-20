from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.application.services.agent_context_service import AgentContextService
from health_agent.domain.entities.user import User
from health_agent.domain.entities.user_profile import UserProfile


class UserProfileUseCases:
    """Use cases related to technical users and business user profiles."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        agent_context_service: AgentContextService,
    ) -> None:
        self._uow_factory = uow_factory
        self._agent_context_service = agent_context_service

    from uuid import UUID


    async def get_user_profile_id_by_telegram_id(
        self,
        *,
        telegram_user_id: int,
    ) -> UUID:
        async with self._uow_factory() as uow:
            user = await uow.users.get_user_by_telegram_id(telegram_user_id)
            if user is None:
                raise ValueError(
                    f"User with telegram_user_id={telegram_user_id} not found."
                )

            profile = await uow.users.get_profile_by_user_id(user.id)
            if profile is None:
                raise ValueError(f"UserProfile for user_id={user.id} not found.")

            return profile.id

    async def create_user_profile(
        self,
        *,
        telegram_user_id: int,
        telegram_chat_id: int,
        username: str | None = None,
        display_name: str | None = None,
        language: str = "ru",
        timezone: str = "Europe/Amsterdam",
        communication_style: str | None = None,
        general_notes: str | None = None,
    ) -> UserProfile:
        async with self._uow_factory() as uow:
            existing_user = await uow.users.get_user_by_telegram_id(telegram_user_id)
            if existing_user is not None:
                existing_profile = await uow.users.get_profile_by_user_id(existing_user.id)
                if existing_profile is not None:
                    raise ValueError(
                        f"UserProfile already exists for telegram_user_id={telegram_user_id}."
                    )

                user = existing_user
            else:
                user = User(
                    telegram_user_id=telegram_user_id,
                    telegram_chat_id=telegram_chat_id,
                    username=username,
                    display_name=display_name,
                )
                await uow.users.add_user(user)

            profile = UserProfile(
                user_id=user.id,
                language=language,
                timezone=timezone,
            )

            if communication_style is not None:
                profile.update_communication_style(communication_style)

            if general_notes is not None:
                profile.update_notes(general_notes)

            await uow.users.add_profile(profile)
            await uow.commit()

            return profile

    async def update_user_profile(
        self,
        *,
        user_profile_id: UUID,
        language: str | None = None,
        timezone: str | None = None,
        communication_style: str | None = None,
        general_notes: str | None = None,
        is_active: bool | None = None,
    ) -> UserProfile:
        async with self._uow_factory() as uow:
            profile = await uow.users.get_profile_by_id(user_profile_id)
            if profile is None:
                raise ValueError(f"UserProfile with id={user_profile_id} not found.")

            if language is not None:
                profile.language = language

            if timezone is not None:
                profile.update_timezone(timezone)

            if communication_style is not None:
                profile.update_communication_style(communication_style)

            if general_notes is not None:
                profile.update_notes(general_notes)

            if is_active is not None:
                profile.is_active = is_active

            await uow.users.save_profile(profile)
            await uow.commit()

            return profile

    async def get_agent_context_by_telegram_user_id(self, telegram_user_id: int) -> str:
        async with self._uow_factory() as uow:
            context = await self._agent_context_service.build_by_telegram_user_id(
                uow=uow,
                telegram_user_id=telegram_user_id,
            )

            return context.to_prompt_text()

    async def get_agent_context_by_user_profile_id(self, user_profile_id: UUID) -> str:
        async with self._uow_factory() as uow:
            context = await self._agent_context_service.build_by_user_profile_id(
                uow=uow,
                user_profile_id=user_profile_id,
            )

            return context.to_prompt_text()