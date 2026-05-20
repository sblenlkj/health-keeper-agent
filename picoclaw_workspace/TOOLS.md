# MCP Tool Policy

This file is compact because detailed procedures live in skills.

## Core Rule

```text
Tools     -> change state
Resources -> read state
Skills    -> workflow procedures
```

Do not use a write tool when a read-only resource is enough.

## Critical ID Rule

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal database UUID
```

Never pass Telegram ID as `user_profile_id`.

For private Telegram chats, `telegram_user_id == telegram_chat_id`.

If session metadata exposes `direct:<telegram_id>`, use it as both Telegram fields. If not, ask the user.

## Tools

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

Optional deployments may expose activate/deactivate tools. If unavailable, do not invent them.

## Resources

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

Do not use several skills when one direct tool/resource action is clear.
