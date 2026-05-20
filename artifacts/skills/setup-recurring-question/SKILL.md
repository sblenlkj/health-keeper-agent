---
name: setup-recurring-question
description: Configure a recurring scheduled question for a tracking target.
---

# Skill: Setup Recurring Question

Use this skill when the user wants to be asked a recurring health question.

Example: `Every evening, ask me what I ate and whether I had stomach symptoms.`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Ensure a relevant target exists by reading `health-agent://tracking-targets/{user_profile_id}`; reuse or create one.
3. Read `health-agent://schedule-crons/{user_profile_id}`.
4. Reuse a suitable schedule or call `create_schedule_cron(...)`.
5. Call `create_question(tracking_target_id=..., schedule_cron_id=..., text=...)`.

The backend executes cron jobs later. Do not manually run the cron.

