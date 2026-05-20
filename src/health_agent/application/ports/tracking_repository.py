from __future__ import annotations

from typing import Protocol
from uuid import UUID

from health_agent.domain.entities.medicine import Medicine
from health_agent.domain.entities.question import Question
from health_agent.domain.entities.reminder import Reminder
from health_agent.domain.entities.schedule_cron import ScheduleCron
from health_agent.domain.entities.tracking_target import TrackingTarget


class TrackingRepository(Protocol):
    """Repository for observation configuration.

    This repository groups closely related configuration entities:
    tracking targets, schedule crons, questions, medicines, and reminders.
    """

    async def add_tracking_target(self, target: TrackingTarget) -> None:
        ...

    async def get_tracking_target_by_id(
        self,
        tracking_target_id: UUID,
    ) -> TrackingTarget | None:
        ...

    async def list_tracking_targets(
        self,
        user_profile_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[TrackingTarget]:
        ...

    async def save_tracking_target(self, target: TrackingTarget) -> None:
        ...

    async def add_schedule_cron(self, schedule: ScheduleCron) -> None:
        ...

    async def get_schedule_cron_by_id(
        self,
        schedule_cron_id: UUID,
    ) -> ScheduleCron | None:
        ...

    async def list_schedule_crons(
        self,
        *,
        user_profile_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[ScheduleCron]:
        ...

    async def save_schedule_cron(self, schedule: ScheduleCron) -> None:
        ...

    async def add_question(self, question: Question) -> None:
        ...

    async def list_questions_by_target(
        self,
        tracking_target_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Question]:
        ...

    async def list_questions_by_schedule(
        self,
        schedule_cron_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Question]:
        ...

    async def save_question(self, question: Question) -> None:
        ...

    async def add_medicine(self, medicine: Medicine) -> None:
        ...

    async def get_medicine_by_id(self, medicine_id: UUID) -> Medicine | None:
        ...

    async def list_medicines_by_target(
        self,
        tracking_target_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Medicine]:
        ...

    async def save_medicine(self, medicine: Medicine) -> None:
        ...

    async def add_reminder(self, reminder: Reminder) -> None:
        ...

    async def list_reminders_by_medicine(
        self,
        medicine_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Reminder]:
        ...

    async def list_reminders_by_schedule(
        self,
        schedule_cron_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Reminder]:
        ...

    async def save_reminder(self, reminder: Reminder) -> None:
        ...