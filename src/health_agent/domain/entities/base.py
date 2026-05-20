from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True, kw_only=True)
class BaseEntity:
    """Base domain entity with internal UUID identity."""

    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True, kw_only=True)
class BaseTitleEntity(BaseEntity):
    """Base entity with title and optional description."""

    title: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(f"{self.__class__.__name__} title must not be empty.")

        if self.description is not None and not self.description.strip():
            raise ValueError(
                f"{self.__class__.__name__} description must not be empty if provided."
            )