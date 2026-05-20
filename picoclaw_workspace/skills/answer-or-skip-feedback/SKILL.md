---
name: answer-or-skip-feedback
description: Match a user answer to pending feedback and answer or skip the item using read-only feedback tools first.
---

# Skill: Answer Or Skip Feedback

Use this skill when the user answers a pending item or wants to skip it.

Examples: `I took magnesium. No stomach reaction.`, `I forgot, skip this one.`, `No symptoms today.`

## Tools

First call:

```text
list_pending_feedback(user_profile_id)
```

Then call:

```text
answer_feedback(...)
skip_feedback(...)
```

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `list_pending_feedback(user_profile_id)`.
3. Match the user's message to the most likely pending item.
4. If the user answers several pending items in one message, answer all clearly matched items.
5. If the user answered clearly, call `answer_feedback(...)`.
6. If the user wants to skip an item, call `skip_feedback(...)`.
7. If multiple items are ambiguous, ask one concise clarifying question.
8. Confirm briefly what was saved or skipped.

Do not create an observation for routine feedback. Create an observation only for notable facts such as strong symptoms, clear worsening, important improvements, or explicit "remember this".

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

