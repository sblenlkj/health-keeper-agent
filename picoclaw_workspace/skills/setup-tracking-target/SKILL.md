---
name: setup-tracking-target
description: Create or reuse a long-lived health tracking target using read-only tools first.
---

# Skill: Setup Tracking Target

Use this skill when the user wants to start tracking a health topic.

Examples: `I want to track digestion.`, `Track my leg pain.`, `Let's monitor my sleep.`

## Tool

Before creating a new target, call:

```text
list_user_tracking_targets(user_profile_id, active_only=True)
```

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Call `list_user_tracking_targets(user_profile_id, active_only=True)`.
3. If a suitable active target exists, reuse it.
4. Otherwise call `create_tracking_target(...)`.

Use short stable lowercase codes:

```text
digestion
leg_pain
headache
sleep
general_wellbeing
```

Confirm the created or reused target and include `tracking_target_id` if available.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

