---
name: review-pending-feedback
description: List pending feedback items that the user should answer using read-only tools.
---

# Skill: Review Pending Feedback

Use this skill when the user asks what they need to answer.

Examples: `What do I need to answer?`, `Do I have pending questions?`, `Show pending feedback.`, `Do you have questions for me today?`

## Tool

Use:

```text
list_pending_feedback(user_profile_id)
```

Do not try to read `health-agent://pending-feedback/{user_profile_id}` directly in Telegram runtime.

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `list_pending_feedback(user_profile_id)`.
3. Show a concise list of pending items.
4. Include enough context: question/reminder text and creation time if useful.
5. Ask which item the user wants to answer first, or invite them to answer all in one message.

Do not answer feedback yourself. Do not create observations.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

