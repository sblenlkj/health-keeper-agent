from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from health_agent.adapters.inbound.mcp.prompts import register_prompts
from health_agent.adapters.inbound.mcp.resources import register_resources
from health_agent.adapters.inbound.mcp.tools_extra import register_extra_tools
from health_agent.adapters.inbound.mcp.tools import register_tools
from health_agent.application.use_cases.feedback_use_cases import FeedbackUseCases
from health_agent.application.use_cases.observation_use_cases import ObservationUseCases
from health_agent.application.use_cases.schedule_management_use_cases import (
    ScheduleManagementUseCases,
)
from health_agent.application.use_cases.tracking_use_cases import TrackingUseCases
from health_agent.application.use_cases.user_profile_use_cases import (
    UserProfileUseCases,
)


def create_mcp_server(
    *,
    user_profile_use_cases: UserProfileUseCases,
    tracking_use_cases: TrackingUseCases,
    schedule_management_use_cases: ScheduleManagementUseCases,
    feedback_use_cases: FeedbackUseCases,
    observation_use_cases: ObservationUseCases,
) -> FastMCP:
    mcp = FastMCP("health-agent")

    register_tools(
        mcp,
        user_profile_use_cases=user_profile_use_cases,
        tracking_use_cases=tracking_use_cases,
        schedule_management_use_cases=schedule_management_use_cases,
        feedback_use_cases=feedback_use_cases,
        observation_use_cases=observation_use_cases,
    )

    register_extra_tools(
        mcp,
        user_profile_use_cases=user_profile_use_cases,
        tracking_use_cases=tracking_use_cases,
        schedule_management_use_cases=schedule_management_use_cases,
        feedback_use_cases=feedback_use_cases,
        observation_use_cases=observation_use_cases,
    )

    register_resources(
        mcp,
        user_profile_use_cases=user_profile_use_cases,
        tracking_use_cases=tracking_use_cases,
        schedule_management_use_cases=schedule_management_use_cases,
        feedback_use_cases=feedback_use_cases,
        observation_use_cases=observation_use_cases,
    )
    register_prompts(mcp)

    return mcp