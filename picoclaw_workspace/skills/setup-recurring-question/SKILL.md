---
name: setup-recurring-question
description: Configure a recurring scheduled question for a tracking target using read-only tools before creating state.
---

# Skill: Setup Recurring Question

Use this skill when the user wants to be asked a recurring health question.

Example: `Every evening, ask me what I ate and whether I had stomach symptoms.`

## Read Before Writing

Use read-only tools before creating new state:

- `list_user_tracking_targets(user_profile_id, active_only=True)`
- `list_user_schedule_crons(user_profile_id, active_only=True)`
- `list_tracking_target_questions(tracking_target_id, active_only=True)`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `list_user_tracking_targets(...)`; reuse a relevant target or create one.
3. Call `list_user_schedule_crons(...)`; reuse a suitable schedule whenever possible.
4. If no suitable schedule exists, call `create_schedule_cron(...)`.
5. Call `list_tracking_target_questions(...)` to avoid duplicate questions.
6. Call `create_question(tracking_target_id=..., schedule_cron_id=..., text=...)` if needed.

The backend executes cron jobs later. Do not manually run the cron.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

