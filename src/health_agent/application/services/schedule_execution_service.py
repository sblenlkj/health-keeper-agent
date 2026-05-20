from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.message_sender import MessageSender
from health_agent.application.ports.unit_of_work import UnitOfWork
from health_agent.application.services.feedback_service import FeedbackService

import logging

logger = logging.getLogger(__name__)

class ScheduleExecutionService:
    """Executes a fired ScheduleCron.

    The scheduler adapter decides when a cron fires.
    The use case owns the UnitOfWork and transaction boundary.
    This service decides what business actions happen after the cron fires.
    """

    def __init__(
        self,
        *,
        feedback_service: FeedbackService,
        message_sender: MessageSender,
    ) -> None:
        self._feedback_service = feedback_service
        self._message_sender = message_sender

    async def execute(
        self,
        *,
        uow: UnitOfWork,
        schedule_cron_id: UUID,
    ) -> None:
        schedule = await uow.tracking.get_schedule_cron_by_id(schedule_cron_id)
        if schedule is None:
            raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

        if not schedule.is_active:
            return

        profile = await uow.users.get_profile_by_id(schedule.user_profile_id)
        if profile is None:
            raise ValueError(
                f"UserProfile with id={schedule.user_profile_id} not found."
            )

        if not profile.is_active:
            return

        user = await uow.users.get_user_by_id(profile.user_id)
        if user is None:
            raise ValueError(f"User with id={profile.user_id} not found.")

        questions = await uow.tracking.list_questions_by_schedule(
            schedule.id,
            active_only=True,
        )
        reminders = await uow.tracking.list_reminders_by_schedule(
            schedule.id,
            active_only=True,
        )

        feedback_texts: list[str] = []
        reminder_messages: list[str] = []

        for question in questions:
            target = await uow.tracking.get_tracking_target_by_id(
                question.tracking_target_id,
            )
            if target is None or not target.is_active:
                continue

            item = self._feedback_service.create_from_question(
                user_profile_id=profile.id,
                question=question,
            )
            await uow.feedback.add_feedback_item(item)
            feedback_texts.append(item.text)

        for reminder in reminders:
            medicine = await uow.tracking.get_medicine_by_id(reminder.medicine_id)
            if medicine is None or not medicine.is_active:
                continue

            reminder_messages.append(reminder.message)

            item = self._feedback_service.create_from_reminder(
                user_profile_id=profile.id,
                reminder=reminder,
            )
            if item is not None:
                await uow.feedback.add_feedback_item(item)
                feedback_texts.append(item.text)

        logger.info("Executing schedule cron %s", schedule_cron_id)
        logger.info(
            "Schedule cron %s created %s feedback items and %s reminder messages",
            schedule_cron_id,
            len(feedback_texts),
            len(reminder_messages),
        )

        if reminder_messages or feedback_texts:
            await self._message_sender.send_message(
                chat_id=user.telegram_chat_id,
                text=self._build_message(
                    reminder_messages=reminder_messages,
                    feedback_texts=feedback_texts,
                ),
            )

    @staticmethod
    def _build_message(
        *,
        reminder_messages: list[str],
        feedback_texts: list[str],
    ) -> str:
        parts: list[str] = []

        if reminder_messages:
            parts.append("Напоминания:")
            parts.extend(f"- {message}" for message in reminder_messages)

        if feedback_texts:
            if parts:
                parts.append("")

            parts.append("Вопросы:")
            parts.extend(f"- {text}" for text in feedback_texts)

        return "\n".join(parts)