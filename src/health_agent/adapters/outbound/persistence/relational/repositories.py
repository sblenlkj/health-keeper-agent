from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from health_agent.adapters.outbound.persistence.relational.models import (
    FeedbackItemModel,
    MedicineModel,
    ObservationModel,
    QuestionModel,
    ReminderModel,
    ScheduleCronModel,
    TrackingTargetModel,
    UserModel,
    UserProfileModel,
)
from health_agent.domain.entities.feedback_item import FeedbackItem, FeedbackItemStatus
from health_agent.domain.entities.medicine import Medicine, MedicineKind
from health_agent.domain.entities.observation import Observation
from health_agent.domain.entities.question import Question
from health_agent.domain.entities.reminder import Reminder
from health_agent.domain.entities.schedule_cron import ScheduleCron
from health_agent.domain.entities.tracking_target import (
    TrackingTarget,
    TrackingTargetCode,
)
from health_agent.domain.entities.user import User
from health_agent.domain.entities.user_profile import UserProfile
from health_agent.domain.value_objects.time_window import TimeWindow


class SqlAlchemyUserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.telegram_user_id == telegram_user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_user(model) if model else None

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return self._to_user(model) if model else None

    async def add_user(self, user: User) -> None:
        self._session.add(self._to_user_model(user))

    async def get_profile_by_user_id(self, user_id: UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_profile(model) if model else None

    async def get_profile_by_id(self, user_profile_id: UUID) -> UserProfile | None:
        model = await self._session.get(UserProfileModel, user_profile_id)
        return self._to_profile(model) if model else None

    async def add_profile(self, profile: UserProfile) -> None:
        self._session.add(self._to_profile_model(profile))

    async def save_profile(self, profile: UserProfile) -> None:
        await self._session.merge(self._to_profile_model(profile))

    @staticmethod
    def _to_user(model: UserModel) -> User:
        return User(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            telegram_chat_id=model.telegram_chat_id,
            username=model.username,
            display_name=model.display_name,
        )

    @staticmethod
    def _to_user_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            telegram_user_id=user.telegram_user_id,
            telegram_chat_id=user.telegram_chat_id,
            username=user.username,
            display_name=user.display_name,
        )

    @staticmethod
    def _to_profile(model: UserProfileModel) -> UserProfile:
        return UserProfile(
            id=model.id,
            user_id=model.user_id,
            language=model.language,
            timezone=model.timezone,
            communication_style=model.communication_style,
            general_notes=model.general_notes,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_profile_model(profile: UserProfile) -> UserProfileModel:
        return UserProfileModel(
            id=profile.id,
            user_id=profile.user_id,
            language=profile.language,
            timezone=profile.timezone,
            communication_style=profile.communication_style,
            general_notes=profile.general_notes,
            is_active=profile.is_active,
        )


class SqlAlchemyTrackingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_tracking_target(self, target: TrackingTarget) -> None:
        self._session.add(self._to_tracking_target_model(target))

    async def get_tracking_target_by_id(
        self,
        tracking_target_id: UUID,
    ) -> TrackingTarget | None:
        model = await self._session.get(TrackingTargetModel, tracking_target_id)
        return self._to_tracking_target(model) if model else None

    async def list_tracking_targets(
        self,
        user_profile_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[TrackingTarget]:
        statement = select(TrackingTargetModel).where(
            TrackingTargetModel.user_profile_id == user_profile_id
        )

        if active_only:
            statement = statement.where(TrackingTargetModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_tracking_target(model) for model in result.scalars().all()]

    async def save_tracking_target(self, target: TrackingTarget) -> None:
        await self._session.merge(self._to_tracking_target_model(target))

    async def add_schedule_cron(self, schedule: ScheduleCron) -> None:
        self._session.add(self._to_schedule_cron_model(schedule))

    async def get_schedule_cron_by_id(
        self,
        schedule_cron_id: UUID,
    ) -> ScheduleCron | None:
        model = await self._session.get(ScheduleCronModel, schedule_cron_id)
        return self._to_schedule_cron(model) if model else None

    async def list_schedule_crons(
        self,
        *,
        user_profile_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[ScheduleCron]:
        statement = select(ScheduleCronModel)

        if user_profile_id is not None:
            statement = statement.where(
                ScheduleCronModel.user_profile_id == user_profile_id
            )

        if active_only:
            statement = statement.where(ScheduleCronModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_schedule_cron(model) for model in result.scalars().all()]

    async def save_schedule_cron(self, schedule: ScheduleCron) -> None:
        await self._session.merge(self._to_schedule_cron_model(schedule))

    async def add_question(self, question: Question) -> None:
        self._session.add(self._to_question_model(question))

    async def list_questions_by_target(
        self,
        tracking_target_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Question]:
        statement = select(QuestionModel).where(
            QuestionModel.tracking_target_id == tracking_target_id
        )

        if active_only:
            statement = statement.where(QuestionModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_question(model) for model in result.scalars().all()]

    async def list_questions_by_schedule(
        self,
        schedule_cron_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Question]:
        statement = select(QuestionModel).where(
            QuestionModel.schedule_cron_id == schedule_cron_id
        )

        if active_only:
            statement = statement.where(QuestionModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_question(model) for model in result.scalars().all()]

    async def save_question(self, question: Question) -> None:
        await self._session.merge(self._to_question_model(question))

    async def add_medicine(self, medicine: Medicine) -> None:
        self._session.add(self._to_medicine_model(medicine))

    async def get_medicine_by_id(self, medicine_id: UUID) -> Medicine | None:
        model = await self._session.get(MedicineModel, medicine_id)
        return self._to_medicine(model) if model else None

    async def list_medicines_by_target(
        self,
        tracking_target_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Medicine]:
        statement = select(MedicineModel).where(
            MedicineModel.tracking_target_id == tracking_target_id
        )

        if active_only:
            statement = statement.where(MedicineModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_medicine(model) for model in result.scalars().all()]

    async def save_medicine(self, medicine: Medicine) -> None:
        await self._session.merge(self._to_medicine_model(medicine))

    async def add_reminder(self, reminder: Reminder) -> None:
        self._session.add(self._to_reminder_model(reminder))

    async def list_reminders_by_medicine(
        self,
        medicine_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Reminder]:
        statement = select(ReminderModel).where(
            ReminderModel.medicine_id == medicine_id
        )

        if active_only:
            statement = statement.where(ReminderModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_reminder(model) for model in result.scalars().all()]

    async def list_reminders_by_schedule(
        self,
        schedule_cron_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Reminder]:
        statement = select(ReminderModel).where(
            ReminderModel.schedule_cron_id == schedule_cron_id
        )

        if active_only:
            statement = statement.where(ReminderModel.is_active.is_(True))

        result = await self._session.execute(statement)
        return [self._to_reminder(model) for model in result.scalars().all()]

    async def save_reminder(self, reminder: Reminder) -> None:
        await self._session.merge(self._to_reminder_model(reminder))

    @staticmethod
    def _to_tracking_target(model: TrackingTargetModel) -> TrackingTarget:
        return TrackingTarget(
            id=model.id,
            user_profile_id=model.user_profile_id,
            title=model.title,
            description=model.description,
            code=TrackingTargetCode(model.code),
            is_active=model.is_active,
        )

    @staticmethod
    def _to_tracking_target_model(target: TrackingTarget) -> TrackingTargetModel:
        return TrackingTargetModel(
            id=target.id,
            user_profile_id=target.user_profile_id,
            title=target.title,
            description=target.description,
            code=str(target.code),
            is_active=target.is_active,
        )

    @staticmethod
    def _to_schedule_cron(model: ScheduleCronModel) -> ScheduleCron:
        return ScheduleCron(
            id=model.id,
            user_profile_id=model.user_profile_id,
            title=model.title,
            description=model.description,
            cron=model.cron,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_schedule_cron_model(schedule: ScheduleCron) -> ScheduleCronModel:
        return ScheduleCronModel(
            id=schedule.id,
            user_profile_id=schedule.user_profile_id,
            title=schedule.title,
            description=schedule.description,
            cron=schedule.cron,
            is_active=schedule.is_active,
        )

    @staticmethod
    def _to_question(model: QuestionModel) -> Question:
        return Question(
            id=model.id,
            tracking_target_id=model.tracking_target_id,
            schedule_cron_id=model.schedule_cron_id,
            text=model.text,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_question_model(question: Question) -> QuestionModel:
        return QuestionModel(
            id=question.id,
            tracking_target_id=question.tracking_target_id,
            schedule_cron_id=question.schedule_cron_id,
            text=question.text,
            is_active=question.is_active,
        )

    @staticmethod
    def _to_medicine(model: MedicineModel) -> Medicine:
        return Medicine(
            id=model.id,
            tracking_target_id=model.tracking_target_id,
            title=model.title,
            description=model.description,
            kind=MedicineKind(model.kind),
            is_active=model.is_active,
        )

    @staticmethod
    def _to_medicine_model(medicine: Medicine) -> MedicineModel:
        return MedicineModel(
            id=medicine.id,
            tracking_target_id=medicine.tracking_target_id,
            title=medicine.title,
            description=medicine.description,
            kind=str(medicine.kind),
            is_active=medicine.is_active,
        )

    @staticmethod
    def _to_reminder(model: ReminderModel) -> Reminder:
        return Reminder(
            id=model.id,
            medicine_id=model.medicine_id,
            schedule_cron_id=model.schedule_cron_id,
            message=model.message,
            feedback_question=model.feedback_question,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_reminder_model(reminder: Reminder) -> ReminderModel:
        return ReminderModel(
            id=reminder.id,
            medicine_id=reminder.medicine_id,
            schedule_cron_id=reminder.schedule_cron_id,
            message=reminder.message,
            feedback_question=reminder.feedback_question,
            is_active=reminder.is_active,
        )


class SqlAlchemyFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_feedback_item(self, item: FeedbackItem) -> None:
        self._session.add(self._to_feedback_item_model(item))

    async def get_feedback_item_by_id(
        self,
        feedback_item_id: UUID,
    ) -> FeedbackItem | None:
        model = await self._session.get(FeedbackItemModel, feedback_item_id)
        return self._to_feedback_item(model) if model else None

    async def list_pending_feedback_items(
        self,
        user_profile_id: UUID,
    ) -> list[FeedbackItem]:
        statement = select(FeedbackItemModel).where(
            FeedbackItemModel.user_profile_id == user_profile_id,
            FeedbackItemModel.status == str(FeedbackItemStatus.PENDING),
        )

        result = await self._session.execute(statement)
        return [self._to_feedback_item(model) for model in result.scalars().all()]

    async def list_feedback_items_by_window(
        self,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[FeedbackItem]:
        statement = select(FeedbackItemModel).where(
            FeedbackItemModel.user_profile_id == user_profile_id,
            FeedbackItemModel.created_at >= window.start,
            FeedbackItemModel.created_at < window.end,
        )

        result = await self._session.execute(statement)
        return [self._to_feedback_item(model) for model in result.scalars().all()]

    async def save_feedback_item(self, item: FeedbackItem) -> None:
        await self._session.merge(self._to_feedback_item_model(item))

    async def add_observation(self, observation: Observation) -> None:
        self._session.add(self._to_observation_model(observation))

    async def list_recent_observations(
        self,
        user_profile_id: UUID,
        *,
        limit: int = 20,
    ) -> list[Observation]:
        statement = (
            select(ObservationModel)
            .where(ObservationModel.user_profile_id == user_profile_id)
            .order_by(ObservationModel.recorded_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(statement)
        return [self._to_observation(model) for model in result.scalars().all()]

    async def list_observations_by_window(
        self,
        user_profile_id: UUID,
        window: TimeWindow,
    ) -> list[Observation]:
        statement = select(ObservationModel).where(
            ObservationModel.user_profile_id == user_profile_id,
            ObservationModel.recorded_at >= window.start,
            ObservationModel.recorded_at < window.end,
        )

        result = await self._session.execute(statement)
        return [self._to_observation(model) for model in result.scalars().all()]

    @staticmethod
    def _to_feedback_item(model: FeedbackItemModel) -> FeedbackItem:
        return FeedbackItem(
            id=model.id,
            user_profile_id=model.user_profile_id,
            text=model.text,
            answer=model.answer,
            status=FeedbackItemStatus(model.status),
            created_at=model.created_at,
            answered_at=model.answered_at,
        )

    @staticmethod
    def _to_feedback_item_model(item: FeedbackItem) -> FeedbackItemModel:
        return FeedbackItemModel(
            id=item.id,
            user_profile_id=item.user_profile_id,
            text=item.text,
            answer=item.answer,
            status=str(item.status),
            created_at=item.created_at,
            answered_at=item.answered_at,
        )

    @staticmethod
    def _to_observation(model: ObservationModel) -> Observation:
        return Observation(
            id=model.id,
            user_profile_id=model.user_profile_id,
            title=model.title,
            description=model.description,
            recorded_at=model.recorded_at,
            occurred_at=model.occurred_at,
        )

    @staticmethod
    def _to_observation_model(observation: Observation) -> ObservationModel:
        return ObservationModel(
            id=observation.id,
            user_profile_id=observation.user_profile_id,
            title=observation.title,
            description=observation.description,
            recorded_at=observation.recorded_at,
            occurred_at=observation.occurred_at,
        )