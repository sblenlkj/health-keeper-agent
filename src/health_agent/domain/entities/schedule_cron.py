from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseTitleEntity

@dataclass(slots=True, kw_only=True)
class ScheduleCron(BaseTitleEntity):
    """Reusable cron schedule for questions and reminders.

    Several questions and reminders can share the same cron to avoid
    sending many small separate messages to the user.
    """

    user_profile_id: UUID
    cron: str

    is_active: bool = True

    def __post_init__(self) -> None:
        BaseTitleEntity.__post_init__(self)

        if not self.cron.strip():
            raise ValueError("Cron expression must not be empty.")

        if len(self.cron.split()) != 5:
            raise ValueError("Cron expression must contain exactly 5 fields.")

    def pause(self) -> None:
        self.is_active = False

    def resume(self) -> None:
        self.is_active = True