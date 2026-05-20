from __future__ import annotations

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


def _parse_resource_datetime(value: str, *, end_of_day: bool = False) -> datetime:
    """Parse resource datetime.

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
        start=_parse_resource_datetime(start),
        end=_parse_resource_datetime(end, end_of_day=True),
    )


def register_resources(
    mcp: FastMCP,
    *,
    user_profile_use_cases: UserProfileUseCases,
    tracking_use_cases: TrackingUseCases,
    schedule_management_use_cases: ScheduleManagementUseCases,
    feedback_use_cases: FeedbackUseCases,
    observation_use_cases: ObservationUseCases,
) -> None:
    @mcp.resource("health-agent://profile/{user_profile_id}")
    async def user_profile_resource(user_profile_id: str) -> str:
        """Compact profile context for the agent."""
        return await user_profile_use_cases.get_agent_context_by_user_profile_id(
            UUID(user_profile_id),
        )

    @mcp.resource("health-agent://tracking-targets/{user_profile_id}")
    async def tracking_targets_resource(user_profile_id: str) -> str:
        """Active tracking targets for the user."""
        targets = await tracking_use_cases.list_tracking_targets(
            user_profile_id=UUID(user_profile_id),
            active_only=True,
        )

        if not targets:
            return "No active tracking targets found."

        return "\n".join(
            f"{target.id}: {target.title} ({target.code})"
            + (f" — {target.description}" if target.description else "")
            for target in targets
        )

    @mcp.resource("health-agent://schedule-crons/{user_profile_id}")
    async def schedule_crons_resource(user_profile_id: str) -> str:
        """Active schedule crons for the user."""
        schedules = await schedule_management_use_cases.list_schedule_crons(
            user_profile_id=UUID(user_profile_id),
            active_only=True,
        )

        if not schedules:
            return "No active schedule crons found."

        return "\n".join(
            f"{schedule.id}: {schedule.title} — {schedule.cron}"
            + (f" — {schedule.description}" if schedule.description else "")
            for schedule in schedules
        )

    @mcp.resource("health-agent://questions/{tracking_target_id}")
    async def questions_resource(tracking_target_id: str) -> str:
        """Active question templates for a tracking target."""
        questions = await tracking_use_cases.list_questions(
            tracking_target_id=UUID(tracking_target_id),
            active_only=True,
        )

        if not questions:
            return "No active questions found."

        return "\n".join(
            f"{question.id}: schedule_cron_id={question.schedule_cron_id} | {question.text}"
            for question in questions
        )

    @mcp.resource("health-agent://medicines/{tracking_target_id}")
    async def medicines_resource(tracking_target_id: str) -> str:
        """Active medicines/supplements/creams/procedures for a tracking target."""
        medicines = await tracking_use_cases.list_medicines(
            tracking_target_id=UUID(tracking_target_id),
            active_only=True,
        )

        if not medicines:
            return "No active medicines found."

        return "\n".join(
            f"{medicine.id}: {medicine.title} ({medicine.kind})"
            + (f" — {medicine.description}" if medicine.description else "")
            for medicine in medicines
        )

    @mcp.resource("health-agent://reminders/{medicine_id}")
    async def reminders_resource(medicine_id: str) -> str:
        """Active reminders for a medicine."""
        reminders = await tracking_use_cases.list_reminders(
            medicine_id=UUID(medicine_id),
            active_only=True,
        )

        if not reminders:
            return "No active reminders found."

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

    @mcp.resource("health-agent://pending-feedback/{user_profile_id}")
    async def pending_feedback_resource(user_profile_id: str) -> str:
        """Pending feedback items for the user."""
        items = await feedback_use_cases.list_pending_feedback_items(
            user_profile_id=UUID(user_profile_id),
        )

        if not items:
            return "No pending feedback items."

        return "\n".join(
            f"{item.id}: created_at={item.created_at.isoformat()} | {item.text}"
            for item in items
        )

    @mcp.resource("health-agent://feedback-window/{user_profile_id}/{start}/{end}")
    async def feedback_window_resource(
        user_profile_id: str,
        start: str,
        end: str,
    ) -> str:
        """Feedback items created inside a time window.

        Prefer date-only values in resource URIs:

        health-agent://feedback-window/{user_profile_id}/2026-05-17/2026-05-18

        Full ISO datetimes are also supported if the MCP client passes them
        correctly.
        """
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

    @mcp.resource("health-agent://observations-window/{user_profile_id}/{start}/{end}")
    async def observations_window_resource(
        user_profile_id: str,
        start: str,
        end: str,
    ) -> str:
        """Important observations recorded inside a time window.

        Prefer date-only values in resource URIs:

        health-agent://observations-window/{user_profile_id}/2026-05-17/2026-05-18
        """
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