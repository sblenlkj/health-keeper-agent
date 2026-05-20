from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from .base import BaseEntity

class FeedbackItemStatus(StrEnum):
    """Status of a question in the daily queue."""

    PENDING = "pending"
    ANSWERED = "answered"
    SKIPPED = "skipped"


@dataclass(slots=True, kw_only=True)
class FeedbackItem(BaseEntity):
    """Question waiting for the user's answer within a day.

    It can be created from a regular Question or from a Reminder feedback question.
    It is attached to a DayCard by user_id and timestamp range, not by FK.
    """

    user_profile_id: UUID
    text: str

    answer: str | None = None
    status: FeedbackItemStatus = FeedbackItemStatus.PENDING

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    answered_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Feedback item text must not be empty.")


    def answer_with(self, answer: str) -> None:
        if not answer.strip():
            raise ValueError("Feedback item answer must not be empty.")

        self.answer = answer
        self.status = FeedbackItemStatus.ANSWERED
        self.answered_at = datetime.now(UTC)

    def skip(self) -> None:
        self.status = FeedbackItemStatus.SKIPPED