---
name: analyze-known-state
description: Read existing profile, targets, feedback, and observations to answer analysis questions without writing state.
---

# Skill: Analyze Known State

Use this skill when the user asks what is already known or asks for analysis.

Examples: `What do you know about me?`, `What do I track?`, `What hurts for me?`, `Analyze my recent state.`

## Critical Rule

This is read-only. Do not create observations, tracking targets, schedules, or feedback.

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Read `health-agent://profile/{user_profile_id}` and `health-agent://tracking-targets/{user_profile_id}`.
3. If the user asks about unresolved questions, read `health-agent://pending-feedback/{user_profile_id}`.
4. If the user asks about history or trends, read relevant feedback/observation windows.
5. If needed, inspect target details through questions, medicines, and reminders resources.

## Answer Structure

Use: Recorded facts, Possible patterns, Unclear points, Suggested next tracking steps.

Do not diagnose, prescribe, or change treatment.

