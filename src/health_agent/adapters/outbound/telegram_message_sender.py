from __future__ import annotations

import httpx


class TelegramMessageSender:
    """Telegram implementation of MessageSender port."""

    def __init__(
        self,
        *,
        bot_token: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._bot_token = bot_token
        self._timeout_seconds = timeout_seconds

    async def send_message(self, chat_id: int, text: str) -> None:
        if not text.strip():
            raise ValueError("Telegram message text must not be empty.")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                },
            )

        response.raise_for_status()