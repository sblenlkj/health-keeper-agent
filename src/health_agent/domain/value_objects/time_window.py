from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """Период времени для анализа событий."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("TimeWindow start must be earlier than end.")

    @classmethod
    def last_hours(cls, hours: int, *, now: datetime | None = None) -> TimeWindow:
        if hours <= 0:
            raise ValueError("Hours must be positive.")

        end = now or datetime.now()
        start = end - timedelta(hours=hours)
        return cls(start=start, end=end)

    @classmethod
    def last_days(cls, days: int, *, now: datetime | None = None) -> TimeWindow:
        if days <= 0:
            raise ValueError("Days must be positive.")

        return cls.last_hours(days * 24, now=now)

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment <= self.end