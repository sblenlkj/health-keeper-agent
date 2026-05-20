from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseEntity

@dataclass(slots=True, kw_only=True)
class Reminder(BaseEntity):
    """Reusable reminder connected to a medicine and schedule.

    A reminder can optionally create a feedback question in the daily queue.
    """

    medicine_id: UUID
    schedule_cron_id: UUID
    message: str

    feedback_question: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("Reminder message must not be empty.")

        if self.feedback_question is not None and not self.feedback_question.strip():
            raise ValueError("Reminder feedback_question must not be empty if provided.")

    def pause(self) -> None:
        self.is_active = False

    def resume(self) -> None:
        self.is_active = True

    def has_feedback_question(self) -> bool:
        return self.feedback_question is not None