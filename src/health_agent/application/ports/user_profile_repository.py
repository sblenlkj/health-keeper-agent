from __future__ import annotations

from typing import Protocol
from uuid import UUID

from health_agent.domain.entities.user import User
from health_agent.domain.entities.user_profile import UserProfile


class UserProfileRepository(Protocol):
    """Repository for technical users and business user profiles.

    We intentionally keep User and UserProfile together because most flows
    start from Telegram identity and immediately need the business profile.
    """

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> User | None:
        ...

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        ...

    async def add_user(self, user: User) -> None:
        ...

    async def get_profile_by_user_id(self, user_id: UUID) -> UserProfile | None:
        ...

    async def get_profile_by_id(self, user_profile_id: UUID) -> UserProfile | None:
        ...

    async def add_profile(self, profile: UserProfile) -> None:
        ...

    async def save_profile(self, profile: UserProfile) -> None:
        ...