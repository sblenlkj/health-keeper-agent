---
name: answer-or-skip-feedback
description: Match a user answer to pending feedback and answer or skip the item.
---

# Skill: Answer Or Skip Feedback

Use this skill when the user answers a pending item or wants to skip it.

Examples: `I took magnesium. No stomach reaction.`, `I forgot, skip this one.`, `No symptoms today.`

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. Read `health-agent://pending-feedback/{user_profile_id}`.
3. Match the user's message to the most likely pending item.
4. If the user answered clearly, call `answer_feedback(...)`.
5. If the user wants to skip, call `skip_feedback(...)`.
6. If multiple items match, ask one clarifying question.
7. Confirm briefly.

Do not create an observation for routine feedback. Create an observation only for notable facts.

