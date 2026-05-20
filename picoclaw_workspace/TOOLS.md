# MCP Tool Policy

This file is compact because detailed procedures live in skills.

## Core Rule

```text
Tools           -> change state
Resources       -> read state
Read-only tools -> fallback read interface when resources are not visible/callable
Skills          -> workflow procedures
```

Prefer resources for read-only state when the runtime exposes them. However, in some PicoClaw/Telegram deployments, MCP resources may not be directly callable by the agent. If you do not see resources, cannot call resources, or the user explicitly asks you to read backend state and resources are unavailable, use the read-only tools listed below.

Do not use a write tool when a resource or read-only tool is enough.

## Critical ID Rule

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal database UUID
```

Never pass Telegram ID as `user_profile_id`.

For private Telegram chats, `telegram_user_id == telegram_chat_id`.

If session metadata exposes `direct:<telegram_id>`, use it as both Telegram fields. If not, ask the user.

## Write Tools

These tools create or update backend state:

- `get_user_profile_id_by_telegram_id`
- `create_user_profile`
- `create_tracking_target`
- `create_schedule_cron`
- `create_question`
- `create_medicine`
- `create_reminder`
- `answer_feedback`
- `skip_feedback`
- `record_observation`

Optional deployments may expose activate/deactivate tools:

- `activate_tracking_target`
- `deactivate_tracking_target`
- `activate_schedule_cron`
- `deactivate_schedule_cron`

If unavailable, do not invent them.

## Resources

Use resources for read-only state when they are available:

```text
health-agent://profile/{user_profile_id}
health-agent://tracking-targets/{user_profile_id}
health-agent://schedule-crons/{user_profile_id}
health-agent://questions/{tracking_target_id}
health-agent://medicines/{tracking_target_id}
health-agent://reminders/{medicine_id}
health-agent://pending-feedback/{user_profile_id}
health-agent://feedback-window/{user_profile_id}/{start}/{end}
health-agent://observations-window/{user_profile_id}/{start}/{end}
```

## Read-Only Tool Fallbacks

If resources are not visible or not callable, use these tools instead:

- `read_user_profile_context(user_profile_id)`
- `list_user_tracking_targets(user_profile_id, active_only=True)`
- `list_user_schedule_crons(user_profile_id, active_only=True)`
- `list_tracking_target_questions(tracking_target_id, active_only=True)`
- `list_tracking_target_medicines(tracking_target_id, active_only=True)`
- `list_medicine_reminders(medicine_id, active_only=True)`
- `list_pending_feedback(user_profile_id)`
- `list_feedback_window(user_profile_id, start, end)`
- `list_observations_window(user_profile_id, start, end)`

These tools must be treated as read-only. They are operational mirrors of the resource layer for runtimes where MCP resources are not reliably exposed to the model.

## Skills

Use skills for multi-step workflows:

- `bootstrap-user-profile`
- `setup-tracking-target`
- `setup-recurring-question`
- `setup-medicine-reminder`
- `review-pending-feedback`
- `answer-or-skip-feedback`
- `record-important-observation`
- `analyze-known-state`

Do not use several skills when one direct tool/resource/read-only-tool action is clear.
