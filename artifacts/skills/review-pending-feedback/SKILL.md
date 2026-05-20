---
name: review-pending-feedback
description: List pending feedback items that the user should answer.
---

# Skill: Review Pending Feedback

Use this skill when the user asks what they need to answer.

Examples: `What do I need to answer?`, `Do I have pending questions?`, `Show pending feedback.`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Read `health-agent://pending-feedback/{user_profile_id}`.
3. Show a concise list of pending items.
4. Include enough context: question text, reminder text if available, related target if available, creation time if useful.
5. Ask which item the user wants to answer first, or invite them to answer all.

Do not answer feedback yourself. Do not create observations.

