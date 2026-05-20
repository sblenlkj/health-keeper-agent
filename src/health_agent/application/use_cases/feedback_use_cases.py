from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.application.services.feedback_service import FeedbackService
from health_agent.domain.entities.feedback_item import FeedbackItem
from health_agent.domain.value_objects.time_window import TimeWindow


class FeedbackUseCases:
    """Use cases for pending feedback questions and answers."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        feedback_service: FeedbackService,
    ) -> None:
        self._uow_factory = uow_factory
        self._feedback_service = feedback_service

    async def list_pending_feedback_items(
        self,
        *,
        user_profile_id: UUID,
    ) -> list[FeedbackItem]:
        async with self._uow_factory() as uow:
            return await uow.feedback.list_pending_feedback_items(
                user_profile_id,
            )

    async def list_feedback_items_by_window(
        self,
        *,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[FeedbackItem]:
        async with self._uow_factory() as uow:
            return await uow.feedback.list_feedback_items_by_window(
                user_profile_id,
                window,
            )

    async def answer_feedback_item(
        self,
        *,
        feedback_item_id: UUID,
        answer: str,
    ) -> FeedbackItem:
        async with self._uow_factory() as uow:
            item = await uow.feedback.get_feedback_item_by_id(feedback_item_id)
            if item is None:
                raise ValueError(f"FeedbackItem with id={feedback_item_id} not found.")

            self._feedback_service.answer(item, answer)

            await uow.feedback.save_feedback_item(item)
            await uow.commit()

            return item

    async def skip_feedback_item(
        self,
        *,
        feedback_item_id: UUID,
    ) -> FeedbackItem:
        async with self._uow_factory() as uow:
            item = await uow.feedback.get_feedback_item_by_id(feedback_item_id)
            if item is None:
                raise ValueError(f"FeedbackItem with id={feedback_item_id} not found.")

            self._feedback_service.skip(item)

            await uow.feedback.save_feedback_item(item)
            await uow.commit()

            return item