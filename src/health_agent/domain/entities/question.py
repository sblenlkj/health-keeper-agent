from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .base import BaseEntity

@dataclass(slots=True, kw_only=True)
class Question(BaseEntity):
    """Reusable question template connected to a tracking target and schedule."""

    tracking_target_id: UUID
    schedule_cron_id: UUID
    text: str

    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Question text must not be empty.")

    def pause(self) -> None:
        self.is_active = False

    def resume(self) -> None:
        self.is_active = True