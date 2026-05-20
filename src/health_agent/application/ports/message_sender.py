from __future__ import annotations

from typing import Protocol


class MessageSender(Protocol):
    """Outbound port for sending messages to the user."""

    async def send_message(self, chat_id: int, text: str) -> None:
        ...