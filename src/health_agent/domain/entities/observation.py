from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .base import BaseTitleEntity

@dataclass(slots=True, kw_only=True)
class Observation(BaseTitleEntity):
    """Important observation recorded by the user or the agent.

    Routine daily answers are stored in DayQuestionQueueItem.
    Observation is reserved for notable facts:
    symptom flare, unusual reaction, important change, or meaningful note.
    """

    user_profile_id: UUID

    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        BaseTitleEntity.__post_init__(self)

    def happened_at(self) -> datetime:
        """Return the best available observation time."""

        return self.occurred_at or self.recorded_at