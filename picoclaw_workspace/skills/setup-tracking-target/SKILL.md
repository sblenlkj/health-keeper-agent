---
name: setup-tracking-target
description: Create or reuse a long-lived health tracking target.
---

# Skill: Setup Tracking Target

Use this skill when the user wants to start tracking a health topic.

Examples: `I want to track digestion.`, `Track my leg pain.`, `Let's monitor my sleep.`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Read `health-agent://tracking-targets/{user_profile_id}`.
3. If a suitable active target exists, reuse it.
4. Otherwise call `create_tracking_target(...)`.

Use short stable lowercase codes: `digestion`, `leg_pain`, `headache`, `sleep`, `general_wellbeing`.

Confirm the created or reused target and include `tracking_target_id` if available.

