from __future__ import annotations

from uuid import UUID

from health_agent.application.ports.unit_of_work import UnitOfWorkFactory
from health_agent.domain.entities.medicine import Medicine, MedicineKind
from health_agent.domain.entities.question import Question
from health_agent.domain.entities.reminder import Reminder
from health_agent.domain.entities.tracking_target import (
    TrackingTarget,
    TrackingTargetCode,
)


class TrackingUseCases:
    """Use cases for tracking targets, questions, medicines, and reminders."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self._uow_factory = uow_factory

    async def create_tracking_target(
        self,
        *,
        user_profile_id: UUID,
        title: str,
        code: TrackingTargetCode,
        description: str | None = None,
    ) -> TrackingTarget:
        async with self._uow_factory() as uow:
            profile = await uow.users.get_profile_by_id(user_profile_id)
            if profile is None:
                raise ValueError(f"UserProfile with id={user_profile_id} not found.")

            target = TrackingTarget(
                user_profile_id=user_profile_id,
                title=title,
                code=code,
                description=description,
            )

            await uow.tracking.add_tracking_target(target)
            await uow.commit()

            return target

    async def list_tracking_targets(
        self,
        *,
        user_profile_id: UUID,
        active_only: bool = True,
    ) -> list[TrackingTarget]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_tracking_targets(
                user_profile_id,
                active_only=active_only,
            )

    async def update_tracking_target(
        self,
        *,
        tracking_target_id: UUID,
        title: str | None = None,
        description: str | None = None,
        code: TrackingTargetCode | None = None,
        is_active: bool | None = None,
    ) -> TrackingTarget:
        async with self._uow_factory() as uow:
            target = await uow.tracking.get_tracking_target_by_id(
                tracking_target_id,
            )
            if target is None:
                raise ValueError(
                    f"TrackingTarget with id={tracking_target_id} not found."
                )

            if title is not None:
                if not title.strip():
                    raise ValueError("Tracking target title must not be empty.")
                target.title = title

            if description is not None:
                target.description = description

            if code is not None:
                target.code = code

            if is_active is not None:
                target.is_active = is_active

            await uow.tracking.save_tracking_target(target)
            await uow.commit()

            return target

    async def create_question(
        self,
        *,
        tracking_target_id: UUID,
        schedule_cron_id: UUID,
        text: str,
    ) -> Question:
        async with self._uow_factory() as uow:
            target = await uow.tracking.get_tracking_target_by_id(
                tracking_target_id,
            )
            if target is None:
                raise ValueError(
                    f"TrackingTarget with id={tracking_target_id} not found."
                )

            if not target.is_active:
                raise ValueError("Cannot create question for inactive tracking target.")

            schedule = await uow.tracking.get_schedule_cron_by_id(
                schedule_cron_id,
            )
            if schedule is None:
                raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

            question = Question(
                tracking_target_id=tracking_target_id,
                schedule_cron_id=schedule_cron_id,
                text=text,
            )

            await uow.tracking.add_question(question)
            await uow.commit()

            return question

    async def list_questions(
        self,
        *,
        tracking_target_id: UUID,
        active_only: bool = True,
    ) -> list[Question]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_questions_by_target(
                tracking_target_id,
                active_only=active_only,
            )

    async def create_medicine(
        self,
        *,
        tracking_target_id: UUID,
        title: str,
        kind: MedicineKind = MedicineKind.OTHER,
        description: str | None = None,
    ) -> Medicine:
        async with self._uow_factory() as uow:
            target = await uow.tracking.get_tracking_target_by_id(
                tracking_target_id,
            )
            if target is None:
                raise ValueError(
                    f"TrackingTarget with id={tracking_target_id} not found."
                )

            if not target.is_active:
                raise ValueError("Cannot create medicine for inactive tracking target.")

            medicine = Medicine(
                tracking_target_id=tracking_target_id,
                title=title,
                kind=kind,
                description=description,
            )

            await uow.tracking.add_medicine(medicine)
            await uow.commit()

            return medicine

    async def list_medicines(
        self,
        *,
        tracking_target_id: UUID,
        active_only: bool = True,
    ) -> list[Medicine]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_medicines_by_target(
                tracking_target_id,
                active_only=active_only,
            )

    async def create_reminder(
        self,
        *,
        medicine_id: UUID,
        schedule_cron_id: UUID,
        message: str,
        feedback_question: str | None = None,
    ) -> Reminder:
        async with self._uow_factory() as uow:
            medicine = await uow.tracking.get_medicine_by_id(medicine_id)
            if medicine is None:
                raise ValueError(f"Medicine with id={medicine_id} not found.")

            if not medicine.is_active:
                raise ValueError("Cannot create reminder for inactive medicine.")

            schedule = await uow.tracking.get_schedule_cron_by_id(
                schedule_cron_id,
            )
            if schedule is None:
                raise ValueError(f"ScheduleCron with id={schedule_cron_id} not found.")

            reminder = Reminder(
                medicine_id=medicine_id,
                schedule_cron_id=schedule_cron_id,
                message=message,
                feedback_question=feedback_question,
            )

            await uow.tracking.add_reminder(reminder)
            await uow.commit()

            return reminder

    async def list_reminders(
        self,
        *,
        medicine_id: UUID,
        active_only: bool = True,
    ) -> list[Reminder]:
        async with self._uow_factory() as uow:
            return await uow.tracking.list_reminders_by_medicine(
                medicine_id,
                active_only=active_only,
            )