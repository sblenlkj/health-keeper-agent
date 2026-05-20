from __future__ import annotations

import logging
from datetime import datetime, time, timezone
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
from health_agent.domain.value_objects.time_window import TimeWindow


logger = logging.getLogger(__name__)


def _log_tool_call(tool_name: str, **context: object) -> None:
    """Log read-only MCP tool calls without leaking health text."""

    if context:
        context_text = " ".join(f"{key}={value}" for key, value in context.items())
        logger.info("MCP read tool called: %s | %s", tool_name, context_text)
        return

    logger.info("MCP read tool called: %s", tool_name)


def _parse_tool_datetime(value: str, *, end_of_day: bool = False) -> datetime:
    """Parse date/datetime values for read-only tools.

    Supports:
    - YYYY-MM-DD
    - full ISO datetime, for example 2026-05-17T00:00:00+00:00

    Date-only values are interpreted in UTC.
    """

    if "T" not in value:
        parsed_date = datetime.fromisoformat(value).date()
        parsed_time = time.max if end_of_day else time.min
        return datetime.combine(parsed_date, parsed_time, tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed


def _build_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(
        start=_parse_tool_datetime(start),
        end=_parse_tool_datetime(end, end_of_day=True),
    )


def register_extra_tools(
    mcp: FastMCP,
    *,
    user_profile_use_cases: UserProfileUseCases,
    tracking_use_cases: TrackingUseCases,
    schedule_management_use_cases: ScheduleManagementUseCases,
    feedback_use_cases: FeedbackUseCases,
    observation_use_cases: ObservationUseCases,
) -> None:
    """Register read-only MCP tools that mirror MCP resources.

    PicoClaw Telegram runtime did not reliably invoke MCP resources during
    the demo. These tools duplicate the resource layer as explicit tools so
    the LLM can call them through the normal tool-calling interface.

    These tools must not mutate backend state.
    """

    @mcp.tool()
    async def read_user_profile_context(user_profile_id: str) -> str:
        """Read compact profile context for the agent.

        Use this after the user_profile_id is known. This is read-only.
        """
        _log_tool_call(
            "read_user_profile_context",
            user_profile_id=user_profile_id,
        )

        return await user_profile_use_cases.get_agent_context_by_user_profile_id(
            UUID(user_profile_id),
        )

    @mcp.tool()
    async def list_user_tracking_targets(
        user_profile_id: str,
        active_only: bool = True,
    ) -> str:
        """List tracking targets for a user.

        Use this before creating a new tracking target to avoid duplicates.
        This is read-only.
        """
        _log_tool_call(
            "list_user_tracking_targets",
            user_profile_id=user_profile_id,
            active_only=active_only,
        )

        targets = await tracking_use_cases.list_tracking_targets(
            user_profile_id=UUID(user_profile_id),
            active_only=active_only,
        )

        if not targets:
            return "No tracking targets found."

        return "\n".join(
            f"{target.id}: {target.title} ({target.code})"
            + (f" — {target.description}" if target.description else "")
            for target in targets
        )

    @mcp.tool()
    async def list_user_schedule_crons(
        user_profile_id: str,
        active_only: bool = True,
    ) -> str:
        """List schedule crons for a user.

        Use this before creating a new schedule cron to reuse an existing
        schedule when possible. This is read-only.
        """
        _log_tool_call(
            "list_user_schedule_crons",
            user_profile_id=user_profile_id,
            active_only=active_only,
        )

        schedules = await schedule_management_use_cases.list_schedule_crons(
            user_profile_id=UUID(user_profile_id),
            active_only=active_only,
        )

        if not schedules:
            return "No schedule crons found."

        return "\n".join(
            f"{schedule.id}: {schedule.title} — {schedule.cron}"
            + (f" — {schedule.description}" if schedule.description else "")
            for schedule in schedules
        )

    @mcp.tool()
    async def list_tracking_target_questions(
        tracking_target_id: str,
        active_only: bool = True,
    ) -> str:
        """List question templates for a tracking target.

        Use this before creating a new recurring question to avoid duplicates.
        This is read-only.
        """
        _log_tool_call(
            "list_tracking_target_questions",
            tracking_target_id=tracking_target_id,
            active_only=active_only,
        )

        questions = await tracking_use_cases.list_questions(
            tracking_target_id=UUID(tracking_target_id),
            active_only=active_only,
        )

        if not questions:
            return "No questions found."

        return "\n".join(
            f"{question.id}: schedule_cron_id={question.schedule_cron_id} | {question.text}"
            for question in questions
        )

    @mcp.tool()
    async def list_tracking_target_medicines(
        tracking_target_id: str,
        active_only: bool = True,
    ) -> str:
        """List medicines, supplements, creams, or procedures for a tracking target.

        Use this before creating a new medicine/reminder setup to avoid
        duplicates. This is read-only.
        """
        _log_tool_call(
            "list_tracking_target_medicines",
            tracking_target_id=tracking_target_id,
            active_only=active_only,
        )

        medicines = await tracking_use_cases.list_medicines(
            tracking_target_id=UUID(tracking_target_id),
            active_only=active_only,
        )

        if not medicines:
            return "No medicines found."

        return "\n".join(
            f"{medicine.id}: {medicine.title} ({medicine.kind})"
            + (f" — {medicine.description}" if medicine.description else "")
            for medicine in medicines
        )

    @mcp.tool()
    async def list_medicine_reminders(
        medicine_id: str,
        active_only: bool = True,
    ) -> str:
        """List reminders for a medicine/supplement/cream/procedure.

        Use this before creating a new reminder to avoid duplicates.
        This is read-only.
        """
        _log_tool_call(
            "list_medicine_reminders",
            medicine_id=medicine_id,
            active_only=active_only,
        )

        reminders = await tracking_use_cases.list_reminders(
            medicine_id=UUID(medicine_id),
            active_only=active_only,
        )

        if not reminders:
            return "No reminders found."

        return "\n".join(
            f"{reminder.id}: schedule_cron_id={reminder.schedule_cron_id} | "
            f"{reminder.message}"
            + (
                f" | feedback: {reminder.feedback_question}"
                if reminder.feedback_question
                else ""
            )
            for reminder in reminders
        )

    @mcp.tool()
    async def list_pending_feedback(user_profile_id: str) -> str:
        """List pending feedback items for the user.

        Use this when the user asks whether there are questions to answer,
        or before matching a free-text answer to scheduled questions/reminders.
        This is read-only.
        """
        _log_tool_call(
            "list_pending_feedback",
            user_profile_id=user_profile_id,
        )

        items = await feedback_use_cases.list_pending_feedback_items(
            user_profile_id=UUID(user_profile_id),
        )

        if not items:
            return "No pending feedback items."

        return "\n".join(
            f"{item.id}: created_at={item.created_at.isoformat()} | {item.text}"
            for item in items
        )

    @mcp.tool()
    async def list_feedback_window(
        user_profile_id: str,
        start: str,
        end: str,
    ) -> str:
        """List feedback items created inside a time window.

        Prefer date-only values:
        - start: 2026-05-17
        - end: 2026-05-18

        Full ISO datetimes are also supported. This is read-only.
        """
        _log_tool_call(
            "list_feedback_window",
            user_profile_id=user_profile_id,
            start=start,
            end=end,
        )

        window = _build_window(start, end)

        items = await feedback_use_cases.list_feedback_items_by_window(
            user_profile_id=UUID(user_profile_id),
            window=window,
        )

        if not items:
            return "No feedback items found for this time window."

        lines: list[str] = []

        for item in items:
            answer = item.answer if item.answer else "<no answer>"
            answered_at = (
                item.answered_at.isoformat()
                if item.answered_at
                else "not answered"
            )

            lines.append(
                f"{item.created_at.isoformat()} — {item.id} | "
                f"status={item.status} | answered_at={answered_at}\n"
                f"Q: {item.text}\n"
                f"A: {answer}"
            )

        return "\n\n".join(lines)

    @mcp.tool()
    async def list_observations_window(
        user_profile_id: str,
        start: str,
        end: str,
    ) -> str:
        """List important observations recorded inside a time window.

        Prefer date-only values:
        - start: 2026-05-17
        - end: 2026-05-18

        Full ISO datetimes are also supported. This is read-only.
        """
        _log_tool_call(
            "list_observations_window",
            user_profile_id=user_profile_id,
            start=start,
            end=end,
        )

        window = _build_window(start, end)

        observations = await observation_use_cases.list_observations_by_window(
            user_profile_id=UUID(user_profile_id),
            window=window,
        )

        if not observations:
            return "No observations found for this time window."

        return "\n".join(
            f"{observation.recorded_at.isoformat()} — "
            f"{observation.id}: {observation.title}: {observation.description}"
            for observation in observations
        )
