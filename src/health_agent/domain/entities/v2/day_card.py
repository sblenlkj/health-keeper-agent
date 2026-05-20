from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(slots=True)
class DayCard:
    """A user's local day represented as a UTC half-open interval.

    DayCard is not a physical container for observations and queue items.
    Observations and queue items are attached to the day by user_id and
    timestamp range: [utc_start_at, utc_end_at).
    """

    user_id: UUID
    local_date: date
    timezone: str

    id: UUID = field(default_factory=uuid4)

    summary: str | None = None
    utc_start_at: datetime = field(init=False)
    utc_end_at: datetime = field(init=False)

    def __post_init__(self) -> None:
        try:
            tz = ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {self.timezone}") from exc

        local_start = datetime.combine(self.local_date, time.min, tzinfo=tz)
        local_end = local_start + timedelta(days=1)

        self.utc_start_at = local_start.astimezone(UTC)
        self.utc_end_at = local_end.astimezone(UTC)

    def update_summary(self, summary: str | None) -> None:
        self.summary = summary

    def contains(self, moment: datetime) -> bool:
        if moment.tzinfo is None:
            raise ValueError("DayCard.contains expects timezone-aware datetime.")

        moment_utc = moment.astimezone(UTC)
        return self.utc_start_at <= moment_utc < self.utc_end_at