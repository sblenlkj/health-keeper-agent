from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class DayTargetSummaryStatus(StrEnum):
    """Rough daily status for one tracking target."""

    BETTER = "better"
    WORSE = "worse"
    STABLE = "stable"
    UNCLEAR = "unclear"
    NOT_ENOUGH_DATA = "not_enough_data"


@dataclass(slots=True)
class DayTargetSummary:
    """Agent-generated summary for one tracking target inside one DayCard."""

    day_card_id: UUID
    tracking_target_id: UUID
    summary: str

    id: UUID = field(default_factory=uuid4)

    status: DayTargetSummaryStatus = DayTargetSummaryStatus.UNCLEAR
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("Day target summary must not be empty.")