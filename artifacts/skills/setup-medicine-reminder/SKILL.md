---
name: setup-medicine-reminder
description: Configure reminders for medicines, supplements, creams, procedures, or routines.
---

# Skill: Setup Medicine Reminder

Use this skill when the user wants a reminder for a medicine, supplement, cream, procedure, or routine.

Example: `Remind me to take magnesium before lunch. I have lunch at 15:00. Ask me whether I took it.`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Ensure a relevant tracking target exists; read targets, reuse or create one.
3. Read `health-agent://schedule-crons/{user_profile_id}`.
4. Reuse a suitable schedule or call `create_schedule_cron(...)`.
5. Read `health-agent://medicines/{tracking_target_id}`.
6. Reuse an existing medicine/supplement/procedure if present.
7. Otherwise call `create_medicine(...)`.
8. Call `create_reminder(...)`.
9. Explain that FastAPI/APScheduler will execute the reminder.

Use `kind`: `medicine`, `supplement`, `cream`, `procedure`, or `routine`.

Do not give medical advice. Configure only what the user requested.

