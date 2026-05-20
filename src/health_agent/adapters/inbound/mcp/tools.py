from __future__ import annotations

import logging
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from health_agent.application.use_cases.feedback_use_cases import FeedbackUseCases
from health_agent.application.use_cases.observation_use_cases import ObservationUseCases
from health_agent.application.use_cases.schedule_management_use_cases import (
    ScheduleManagementUseCases,
)
from health_agent.application.use_cases.tracking_use_cases import TrackingUseCases
from health_agent.application.use_cases.user_profile_use_cases import (
    UserProfileUseCases,
)
from health_agent.domain.entities.medicine import MedicineKind
from health_agent.domain.entities.tracking_target import TrackingTargetCode


logger = logging.getLogger(__name__)


def _log_tool_call(tool_name: str, **context: object) -> None:
    """Log MCP tool call without leaking sensitive health text."""

    if context:
        context_text = " ".join(f"{key}={value}" for key, value in context.items())
        logger.info("MCP tool called: %s | %s", tool_name, context_text)
        return

    logger.info("MCP tool called: %s", tool_name)


def register_tools(
    mcp: FastMCP,
    *,
    user_profile_use_cases: UserProfileUseCases,
    tracking_use_cases: TrackingUseCases,
    schedule_management_use_cases: ScheduleManagementUseCases,
    feedback_use_cases: FeedbackUseCases,
    observation_use_cases: ObservationUseCases,
    activate_deactivate_tools_flag: bool = True,
) -> None:
    @mcp.tool()
    async def get_user_profile_id_by_telegram_id(telegram_user_id: int) -> str:
        """Get existing business user_profile_id by Telegram user ID.

        Use this tool at the beginning of a session.
        If the profile does not exist, call create_user_profile.
        """
        _log_tool_call(
            "get_user_profile_id_by_telegram_id",
            telegram_user_id=telegram_user_id,
        )


        try:
            profile_id = await user_profile_use_cases.get_user_profile_id_by_telegram_id(
                telegram_user_id=telegram_user_id,
            )
        except ValueError as e:
            return f"NOT_FOUND. No user profile exists for telegram_user_id={telegram_user_id}"

        return str(profile_id)

    @mcp.tool()
    async def create_user_profile(
        telegram_user_id: int,
        telegram_chat_id: int,
        username: str | None = None,
        display_name: str | None = None,
        language: str = "ru",
        timezone: str = "Europe/Amsterdam",
        communication_style: str | None = None,
        general_notes: str | None = None,
    ) -> str:
        """Create a new business user profile for a Telegram user.

        Use this only if get_user_profile_id_by_telegram_id failed because
        the profile does not exist.
        """
        _log_tool_call(
            "create_user_profile",
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            language=language,
            timezone=timezone,
        )

        profile = await user_profile_use_cases.create_user_profile(
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            username=username,
            display_name=display_name,
            language=language,
            timezone=timezone,
            communication_style=communication_style,
            general_notes=general_notes,
        )

        logger.info(
            "User profile created | user_profile_id=%s telegram_user_id=%s",
            profile.id,
            telegram_user_id,
        )

        return f"OK. Created user_profile_id={profile.id}"

    @mcp.tool()
    async def create_tracking_target(
        user_profile_id: str,
        title: str,
        code: TrackingTargetCode,
        description: str | None = None,
    ) -> str:
        """Create a new observation target for the user."""
        _log_tool_call(
            "create_tracking_target",
            user_profile_id=user_profile_id,
            code=code,
        )

        target = await tracking_use_cases.create_tracking_target(
            user_profile_id=UUID(user_profile_id),
            title=title,
            code=code,
            description=description,
        )

        logger.info(
            "Tracking target created | tracking_target_id=%s user_profile_id=%s",
            target.id,
            user_profile_id,
        )

        return f"OK. Created tracking_target_id={target.id}"

    if activate_deactivate_tools_flag:
        @mcp.tool()
        async def deactivate_tracking_target(tracking_target_id: str) -> str:
            """Deactivate a tracking target.

            This does not delete historical data. It only marks the target as inactive.
            """
            _log_tool_call(
                "deactivate_tracking_target",
                tracking_target_id=tracking_target_id,
            )

            target = await tracking_use_cases.update_tracking_target(
                tracking_target_id=UUID(tracking_target_id),
                is_active=False,
            )

            logger.info(
                "Tracking target deactivated | tracking_target_id=%s",
                target.id,
            )

            return f"OK. Deactivated tracking_target_id={target.id}"

        @mcp.tool()
        async def activate_tracking_target(tracking_target_id: str) -> str:
            """Activate a tracking target."""
            _log_tool_call(
                "activate_tracking_target",
                tracking_target_id=tracking_target_id,
            )

            target = await tracking_use_cases.update_tracking_target(
                tracking_target_id=UUID(tracking_target_id),
                is_active=True,
            )

            logger.info(
                "Tracking target activated | tracking_target_id=%s",
                target.id,
            )

            return f"OK. Activated tracking_target_id={target.id}"

    @mcp.tool()
    async def create_schedule_cron(
        user_profile_id: str,
        title: str,
        cron: str,
        description: str | None = None,
    ) -> str:
        """Create a shared cron schedule for questions and reminders.

        Example cron values:
        - 0 9 * * *  -> every day at 09:00 UTC
        - 0 21 * * * -> every day at 21:00 UTC
        """
        _log_tool_call(
            "create_schedule_cron",
            user_profile_id=user_profile_id,
            cron=cron,
        )

        schedule = await schedule_management_use_cases.create_schedule_cron(
            user_profile_id=UUID(user_profile_id),
            title=title,
            cron=cron,
            description=description,
        )

        logger.info(
            "Schedule cron created | schedule_cron_id=%s user_profile_id=%s cron=%s",
            schedule.id,
            user_profile_id,
            cron,
        )

        return f"OK. Created schedule_cron_id={schedule.id}"

    if activate_deactivate_tools_flag:
        @mcp.tool()
        async def deactivate_schedule_cron(schedule_cron_id: str) -> str:
            """Deactivate a schedule cron and pause it in scheduler runtime.

            Use this to stop experimental or no longer needed scheduled jobs.
            """
            _log_tool_call(
                "deactivate_schedule_cron",
                schedule_cron_id=schedule_cron_id,
            )

            schedule = await schedule_management_use_cases.pause_schedule_cron(
                schedule_cron_id=UUID(schedule_cron_id),
            )

            logger.info(
                "Schedule cron deactivated | schedule_cron_id=%s",
                schedule.id,
            )

            return f"OK. Deactivated schedule_cron_id={schedule.id}"

        @mcp.tool()
        async def activate_schedule_cron(schedule_cron_id: str) -> str:
            """Activate a schedule cron and resume it in scheduler runtime."""
            _log_tool_call(
                "activate_schedule_cron",
                schedule_cron_id=schedule_cron_id,
            )

            schedule = await schedule_management_use_cases.resume_schedule_cron(
                schedule_cron_id=UUID(schedule_cron_id),
            )

            logger.info(
                "Schedule cron activated | schedule_cron_id=%s",
                schedule.id,
            )

            return f"OK. Activated schedule_cron_id={schedule.id}"

    @mcp.tool()
    async def create_question(
        tracking_target_id: str,
        schedule_cron_id: str,
        text: str,
    ) -> str:
        """Create a recurring question template for a tracking target."""
        _log_tool_call(
            "create_question",
            tracking_target_id=tracking_target_id,
            schedule_cron_id=schedule_cron_id,
        )

        question = await tracking_use_cases.create_question(
            tracking_target_id=UUID(tracking_target_id),
            schedule_cron_id=UUID(schedule_cron_id),
            text=text,
        )

        logger.info(
            "Question created | question_id=%s tracking_target_id=%s schedule_cron_id=%s",
            question.id,
            tracking_target_id,
            schedule_cron_id,
        )

        return f"OK. Created question_id={question.id}"

    @mcp.tool()
    async def create_medicine(
        tracking_target_id: str,
        title: str,
        kind: MedicineKind | None = None,
        description: str | None = None,
    ) -> str:
        """Create a medicine/supplement/cream/procedure for a tracking target."""
        _log_tool_call(
            "create_medicine",
            tracking_target_id=tracking_target_id,
            kind=kind,
        )

        if kind is None:
            kind = MedicineKind.OTHER
    
        medicine = await tracking_use_cases.create_medicine(
            tracking_target_id=UUID(tracking_target_id),
            title=title,
            kind=kind,
            description=description,
        )

        logger.info(
            "Medicine created | medicine_id=%s tracking_target_id=%s kind=%s",
            medicine.id,
            tracking_target_id,
            kind,
        )

        return f"OK. Created medicine_id={medicine.id}"

    @mcp.tool()
    async def create_reminder(
        medicine_id: str,
        schedule_cron_id: str,
        message: str,
        feedback_question: str | None = None,
    ) -> str:
        """Create a reminder for a medicine.

        If feedback_question is provided, the reminder will also create a
        FeedbackItem after the schedule fires.
        """
        _log_tool_call(
            "create_reminder",
            medicine_id=medicine_id,
            schedule_cron_id=schedule_cron_id,
            has_feedback_question=feedback_question is not None,
        )

        reminder = await tracking_use_cases.create_reminder(
            medicine_id=UUID(medicine_id),
            schedule_cron_id=UUID(schedule_cron_id),
            message=message,
            feedback_question=feedback_question,
        )

        logger.info(
            "Reminder created | reminder_id=%s medicine_id=%s schedule_cron_id=%s",
            reminder.id,
            medicine_id,
            schedule_cron_id,
        )

        return f"OK. Created reminder_id={reminder.id}"

    @mcp.tool()
    async def answer_feedback(feedback_item_id: str, answer: str) -> str:
        """Answer a pending feedback item."""
        _log_tool_call(
            "answer_feedback",
            feedback_item_id=feedback_item_id,
        )

        item = await feedback_use_cases.answer_feedback_item(
            feedback_item_id=UUID(feedback_item_id),
            answer=answer,
        )

        logger.info("Feedback item answered | feedback_item_id=%s", item.id)

        return f"OK. Feedback item answered: {item.id}"

    @mcp.tool()
    async def skip_feedback(feedback_item_id: str) -> str:
        """Skip a pending feedback item."""
        _log_tool_call(
            "skip_feedback",
            feedback_item_id=feedback_item_id,
        )

        item = await feedback_use_cases.skip_feedback_item(
            feedback_item_id=UUID(feedback_item_id),
        )

        logger.info("Feedback item skipped | feedback_item_id=%s", item.id)

        return f"OK. Feedback item skipped: {item.id}"

    @mcp.tool()
    async def record_observation(
        user_profile_id: str,
        title: str,
        description: str,
    ) -> str:
        """Record an important observation.

        Use this for notable facts only, not for every routine answer.
        """
        _log_tool_call(
            "record_observation",
            user_profile_id=user_profile_id,
        )

        observation = await observation_use_cases.record_observation(
            user_profile_id=UUID(user_profile_id),
            title=title,
            description=description,
        )

        logger.info(
            "Observation recorded | observation_id=%s user_profile_id=%s",
            observation.id,
            user_profile_id,
        )

        return f"OK. Created observation_id={observation.id}"