---
name: analyze-known-state
description: Read existing profile, targets, feedback, and observations through read-only tools without writing state.
---

# Skill: Analyze Known State

Use this skill when the user asks what is already known or asks for analysis.

Examples: `What do you know about me?`, `What do I track?`, `What hurts for me?`, `Analyze my recent state.`, `Summarize today.`

## Critical Rule

This is read-only. Do not create observations, tracking targets, schedules, reminders, or feedback answers unless the user explicitly asks for that.

## Read-Only Tools

Use these tools instead of MCP resource URIs:

- `read_user_profile_context(user_profile_id)`
- `list_user_tracking_targets(user_profile_id, active_only=True)`
- `list_user_schedule_crons(user_profile_id, active_only=True)`
- `list_tracking_target_questions(tracking_target_id, active_only=True)`
- `list_tracking_target_medicines(tracking_target_id, active_only=True)`
- `list_medicine_reminders(medicine_id, active_only=True)`
- `list_pending_feedback(user_profile_id)`
- `list_feedback_window(user_profile_id, start, end)`
- `list_observations_window(user_profile_id, start, end)`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `read_user_profile_context(user_profile_id)` for compact context.
3. If the user asks what is being tracked, call `list_user_tracking_targets(...)`.
4. If the user asks about unresolved questions, call `list_pending_feedback(...)`.
5. If the user asks about today, history, or trends, call `list_feedback_window(...)` and `list_observations_window(...)`.
6. If needed, inspect target details with `list_tracking_target_questions(...)`, `list_tracking_target_medicines(...)`, and `list_medicine_reminders(...)`.

## Answer Structure

Use: Recorded facts, Possible patterns, Unclear points, Suggested next tracking steps.

Do not diagnose, prescribe, or change treatment.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

