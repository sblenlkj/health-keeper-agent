from __future__ import annotations

from uuid import UUID

from health_agent.domain.entities.feedback_item import FeedbackItem
from health_agent.domain.entities.question import Question
from health_agent.domain.entities.reminder import Reminder


class FeedbackService:
    """Creates and updates feedback items.

    This service does not use repositories and does not own transactions.
    It only contains reusable application logic for feedback item creation
    and state transitions.
    """

    def create_from_question(
        self,
        *,
        user_profile_id: UUID,
        question: Question,
    ) -> FeedbackItem:
        if not question.is_active:
            raise ValueError("Cannot create feedback item from inactive question.")

        return FeedbackItem(
            user_profile_id=user_profile_id,
            text=question.text,
        )

    def create_from_reminder(
        self,
        *,
        user_profile_id: UUID,
        reminder: Reminder,
    ) -> FeedbackItem | None:
        if not reminder.is_active:
            raise ValueError("Cannot create feedback item from inactive reminder.")

        if reminder.feedback_question is None:
            return None

        return FeedbackItem(
            user_profile_id=user_profile_id,
            text=reminder.feedback_question,
        )

    def answer(self, item: FeedbackItem, answer: str) -> None:
        item.answer_with(answer)

    def skip(self, item: FeedbackItem) -> None:
        item.skip()