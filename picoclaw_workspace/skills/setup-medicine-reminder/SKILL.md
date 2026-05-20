---
name: setup-medicine-reminder
description: Configure reminders for medicines, supplements, creams, procedures, or routines using read-only tools before creating new state.
---

# Skill: Setup Medicine Reminder

Use this skill when the user wants a reminder for a medicine, supplement, cream, procedure, or routine.

Example: `Remind me to take magnesium before lunch. I have lunch at 15:00. Ask me whether I took it.`

## Read Before Writing

Use read-only tools before creating new state:

- `list_user_tracking_targets(user_profile_id, active_only=True)`
- `list_user_schedule_crons(user_profile_id, active_only=True)`
- `list_tracking_target_medicines(tracking_target_id, active_only=True)`
- `list_medicine_reminders(medicine_id, active_only=True)`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `list_user_tracking_targets(...)`; reuse a relevant target or create one.
3. Call `list_user_schedule_crons(...)`; reuse a suitable schedule whenever possible.
4. If no suitable schedule exists, call `create_schedule_cron(...)`.
5. Call `list_tracking_target_medicines(...)`.
6. Reuse an existing medicine/supplement/cream/procedure/routine if present.
7. Otherwise call `create_medicine(...)`.
8. Optionally call `list_medicine_reminders(...)` to avoid duplicate reminders.
9. Call `create_reminder(...)`.
10. Explain that FastAPI/APScheduler will execute the reminder.

Use `kind`: `medicine`, `supplement`, `cream`, `procedure`, or `routine`.

Do not give medical advice. Configure only what the user requested.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

