from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from .base import BaseTitleEntity
from .medicine import Medicine
from .question import Question


class TrackingTargetCode(StrEnum):
    """Known observation target codes."""

    DIGESTION = "digestion"
    LEG_PAIN = "leg_pain"
    JOINT_PAIN = "joint_pain"
    HEADACHE = "headache"
    GENERAL_WELLBEING = "general_wellbeing"
    OTHER = "other"


@dataclass(slots=True, kw_only=True)
class TrackingTarget(BaseTitleEntity):
    """A user-specific observation target.

    This is an aggregate root. Questions and medicines belong to this target.

    Examples:
    - digestion;
    - leg pain;
    - joint pain;
    - headache.
    """

    user_profile_id: UUID
    code: TrackingTargetCode

    questions: list[Question] = field(default_factory=list)
    medicines: list[Medicine] = field(default_factory=list)

    is_active: bool = True

    def __post_init__(self) -> None:
        BaseTitleEntity.__post_init__(self)

    def add_question(self, question: Question) -> None:
        if question.tracking_target_id != self.id:
            raise ValueError("Question belongs to another tracking target.")

        self.questions.append(question)

    def remove_question(self, question_id: UUID) -> None:
        self.questions = [
            question for question in self.questions if question.id != question_id
        ]

    def get_active_questions(self) -> list[Question]:
        return [question for question in self.questions if question.is_active]

    def add_medicine(self, medicine: Medicine) -> None:
        if medicine.tracking_target_id != self.id:
            raise ValueError("Medicine belongs to another tracking target.")

        self.medicines.append(medicine)

    def remove_medicine(self, medicine_id: UUID) -> None:
        self.medicines = [
            medicine for medicine in self.medicines if medicine.id != medicine_id
        ]

    def get_active_medicines(self) -> list[Medicine]:
        return [medicine for medicine in self.medicines if medicine.is_active]

    def pause(self) -> None:
        self.is_active = False

        for question in self.questions:
            question.pause()

        for medicine in self.medicines:
            medicine.pause()

    def resume(self) -> None:
        self.is_active = True

    def has_code(self, code: TrackingTargetCode) -> bool:
        return self.code == code