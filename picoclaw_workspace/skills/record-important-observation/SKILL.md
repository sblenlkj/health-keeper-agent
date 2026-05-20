---
name: record-important-observation
description: Record notable health facts as observations, not routine feedback.
---

# Skill: Record Important Observation

Use this skill when the user reports a notable fact or explicitly asks to remember something.

Examples: `Remember that my leg hurt after walking today.`, `I had strong stomach pain after lunch.`

## Observation vs Feedback

Use `answer_feedback` for routine answers to pending questions.

Use `record_observation` for notable facts:

- strong symptom;
- unusual reaction;
- clear worsening;
- clear improvement;
- important event;
- explicit "remember this".

## Workflow

1. Ensure `user_profile_id`. If missing, use `bootstrap-user-profile`.
2. If the message looks like an answer to a scheduled question, first call `list_pending_feedback(user_profile_id)` and use `answer-or-skip-feedback`.
3. Decide whether the message is routine feedback or a notable observation.
4. If notable, call `record_observation(...)`.
5. Confirm briefly.

Record what the user reported. Do not diagnose or infer causality as fact.

## Runtime Note

In this project, important read operations must use read-only MCP tools from `tools_extra.py`, not raw MCP resource URIs. The Telegram/PicoClaw runtime reliably calls tools, while resources were not reliably callable during the demo.

