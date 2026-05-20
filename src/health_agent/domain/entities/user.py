from __future__ import annotations

from dataclasses import dataclass

from .base import BaseEntity

@dataclass(slots=True, kw_only=True)
class User(BaseEntity):
    """Technical user identity connected to Telegram."""

    telegram_user_id: int
    telegram_chat_id: int

    username: str | None = None
    display_name: str | None = None