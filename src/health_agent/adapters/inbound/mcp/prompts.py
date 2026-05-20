from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
   @mcp.prompt(
      name="analyze_user_state",
      description=(
         "Analyze the user's recorded health state using profile, tracking "
         "targets, pending feedback, feedback windows, observations, and "
         "configuration resources. This is read-only analysis, not diagnosis."
      ),
   )
   def analyze_user_state() -> str:
      return """
You are analyzing the user's recent state using the Health Agent MCP server.

This is a health-observation workflow, not a medical diagnosis workflow.

Goal:
Help the user understand what is visible from their recorded feedback,
observations, tracking targets, medicines, reminders, and schedules.

Use MCP primitives according to this rule:

- Resources are for reading state.
- Tools are for changing state.
- Prompts are for reusable reasoning workflows.

Workflow:

1. Make sure you know the current user_profile_id.

   If you do not know it, use the proper bootstrap flow:
   - call get_user_profile_id_by_telegram_id if telegram_user_id is known;
   - if no profile exists, call create_user_profile.

2. Read the compact profile resource:

   health-agent://profile/{user_profile_id}

3. Check pending unanswered feedback if needed:

   health-agent://pending-feedback/{user_profile_id}

   Use this when the user asks:
   - what remains unanswered;
   - what they still need to answer;
   - what pending questions exist.

4. Read routine feedback for a concrete time window when analyzing recent answers:

   health-agent://feedback-window/{user_profile_id}/{start}/{end}

   Prefer date-only values:

   health-agent://feedback-window/{user_profile_id}/2026-05-17/2026-05-18

   Use this for:
   - daily analysis;
   - weekly analysis;
   - checking what the user answered recently;
   - finding routine patterns.

5. Read important observations for a concrete time window:

   health-agent://observations-window/{user_profile_id}/{start}/{end}

   Prefer date-only values:

   health-agent://observations-window/{user_profile_id}/2026-05-17/2026-05-18

   Use this for:
   - important symptom episodes;
   - notable reactions;
   - unusual events;
   - facts the agent previously recorded as observations.

6. If needed, inspect configuration resources:

   health-agent://tracking-targets/{user_profile_id}
   health-agent://schedule-crons/{user_profile_id}
   health-agent://questions/{tracking_target_id}
   health-agent://medicines/{tracking_target_id}
   health-agent://reminders/{medicine_id}

   Use these resources when you need to understand:
   - what the user is tracking;
   - what questions are configured;
   - what medicines/supplements/creams/procedures are connected;
   - what reminders exist;
   - what schedules exist.

7. Summarize carefully.

   Include:
   - what seems stable;
   - what seems worse;
   - what seems better;
   - what is unclear;
   - what data is missing;
   - what should be tracked next.

8. Do not diagnose.

   You may say:
   - "по записям видно";
   - "похоже на возможную связь";
   - "данных пока мало";
   - "это стоит обсудить с врачом";
   - "лучше продолжить фиксировать".

   Do not say:
   - "это точно из-за...";
   - "у тебя диагноз...";
   - "принимай...";
   - "отмени лекарство...";
   - "измени дозировку...".

9. Use tools only when changing state.

   Use record_observation only for notable facts.

   Good observation examples:
   - strong leg pain after walking;
   - stomach pain started in the evening;
   - unusual reaction after supplement;
   - clear improvement after stopping something;
   - symptom episode that the user explicitly wants to remember.

   Do not record every routine answer as an observation.
   Routine answers should be saved through feedback items.

10. If the user answers a pending feedback item, use answer_feedback.

11. If the user says a pending feedback item is irrelevant, use skip_feedback.

12. If you are unsure, ask one precise follow-up question.

Output style:
- Be concise.
- Prefer bullet points.
- Separate facts from hypotheses.
- Mention when data is missing.
- Do not overuse medical disclaimers.
"""

   @mcp.prompt(
      name="summarize_interaction_for_report",
      description=(
         "Summarize the current Health Keeper interaction for a technical "
         "project report, focusing on user goal, MCP tools/resources/prompts "
         "used, backend effects, persistence, and limitations."
      ),
   )
   def summarize_interaction_for_report() -> str:
      return """
You are summarizing the current interaction for a technical project report.

This is not a medical summary.
This is a technical interaction summary for the Health Agent project.

Goal:
Create a concise but useful summary of what happened during the user-agent interaction.

Use the available conversation context and MCP state when needed.
Do not invent tool calls, IDs, database records, or results.

Context:
The project is a PicoClaw/OpenClaw Telegram agent connected to a custom MCP server.
The MCP server exposes tools, resources, and prompts for a personal health-observation assistant.
The backend uses application use cases, SQLite persistence, and a separate FastAPI scheduler runtime.

Structure the summary exactly like this:

## Interaction Summary

### User Goal

Describe what the user wanted to achieve.

Include:
- the practical task;
- the health-agent scenario;
- whether the user was configuring tracking, testing tools, debugging MCP, or preparing the report.

### Agent Actions

Describe what the agent attempted to do.

Mention:
- which MCP tools were relevant;
- which MCP resources were relevant;
- which MCP prompt was used or should be used;
- whether the agent created, inspected, or analyzed data.

### Created / Updated Entities

List only entities that were actually created or clearly requested.

Possible entities:
- User;
- UserProfile;
- TrackingTarget;
- ScheduleCron;
- Question;
- Medicine;
- Reminder;
- FeedbackItem;
- Observation.

For each entity, include known IDs only if they are visible in the conversation or tool result.

If an ID is unknown, write "unknown".

### Tool Execution

Summarize tool execution.

Include:
- which tool calls succeeded;
- which tool calls failed;
- which tool calls were only attempted as text and did not execute;
- whether the database changed;
- whether MCP logs confirmed execution.

Be factual.

### Resources and Prompts

Mention resources/prompts that were used or should be used.

Resources may include:
- health-agent://profile/{user_profile_id}
- health-agent://tracking-targets/{user_profile_id}
- health-agent://schedule-crons/{user_profile_id}
- health-agent://questions/{tracking_target_id}
- health-agent://medicines/{tracking_target_id}
- health-agent://reminders/{medicine_id}
- health-agent://pending-feedback/{user_profile_id}
- health-agent://feedback-window/{user_profile_id}/{start}/{end}
- health-agent://observations-window/{user_profile_id}/{start}/{end}

Prompts may include:
- analyze_user_state
- summarize_interaction_for_report
"""