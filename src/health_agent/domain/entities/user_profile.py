from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import UUID

from .base import BaseEntity


@dataclass(slots=True, kw_only=True)
class UserProfile(BaseEntity):
    """User-specific profile used for personalization and local day boundaries."""

    user_id: UUID

    timezone: str = "Europe/Amsterdam"
    communication_style: str = "Коротко, прямо, без сюсюканья."
    general_notes: str | None = None

    language: str = "ru"
    is_active: bool = True

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def __post_init__(self) -> None:
        self._validate_timezone(self.timezone)

    def update_notes(self, notes: str | None) -> None:
        self.general_notes = notes

    def update_timezone(self, timezone: str) -> None:
        self._validate_timezone(timezone)
        self.timezone = timezone

    def update_communication_style(self, style: str) -> None:
        if not style.strip():
            raise ValueError("Communication style must not be empty.")

        self.communication_style = style

    @staticmethod
    def _validate_timezone(timezone: str) -> None:
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {timezone}") from exc