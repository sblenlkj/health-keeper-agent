from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from .base import BaseTitleEntity

class MedicineKind(StrEnum):
    """Type of medicine-like item.

    The word Medicine is used broadly here:
    medicines, supplements, creams, ointments, procedures, and similar items.
    """

    MEDICINE = "medicine"
    SUPPLEMENT = "supplement"
    CREAM = "cream"
    OINTMENT = "ointment"
    PROCEDURE = "procedure"
    OTHER = "other"


@dataclass(slots=True, kw_only=True)
class Medicine(BaseTitleEntity):
    """Something the user takes or applies for a tracking target."""

    tracking_target_id: UUID

    kind: MedicineKind = MedicineKind.OTHER
    is_active: bool = True

    def __post_init__(self) -> None:
        BaseTitleEntity.__post_init__(self)

    def pause(self) -> None:
        self.is_active = False

    def resume(self) -> None:
        self.is_active = True