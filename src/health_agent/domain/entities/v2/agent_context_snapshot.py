from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class AgentContextSnapshot:
    """Денормализованный контекст пользователя для агента.

    Это не source of truth. Источник правды — нормальные доменные сущности.
    Snapshot нужен, чтобы stateless agent/tool call быстро получил компактный
    контекст пользователя.
    """

    user_id: UUID
    data: dict[str, Any]
    id: UUID = field(default_factory=uuid4)

    version: int = 1
    rebuilt_at: datetime = field(default_factory=datetime.now)

    def bump_version(self) -> None:
        self.version += 1
        self.rebuilt_at = datetime.now()

    def replace_data(self, data: dict[str, Any]) -> None:
        self.data = data
        self.bump_version()

    def get_prompt_context(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "version": self.version,
            "rebuilt_at": self.rebuilt_at.isoformat(),
            "data": self.data,
        }