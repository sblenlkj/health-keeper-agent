---
name: bootstrap-user-profile
description: Resolve or create the current internal Health Agent user profile before database operations.
---

# Skill: Bootstrap User Profile

Use this skill when a request needs backend/database access and the internal `user_profile_id` is not established.

## Goal

Resolve the current user to an internal `user_profile_id`.

## ID Rules

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal database UUID
```

Rules:

- `telegram_user_id` is not `user_profile_id`.
- `telegram_chat_id` is not `user_profile_id`.
- `user_profile_id` must be returned by the backend.
- Never invent UUIDs.
- Never use placeholders.
- For private Telegram chats, `telegram_user_id == telegram_chat_id`.

## Workflow

1. Check whether a valid internal `user_profile_id` is already known in the current interaction or session.
2. If yes, reuse it. Do not bootstrap again.
3. If no `user_profile_id` is known, check whether the current conversation/session exposes `direct:<telegram_id>`.
4. For this MVP, only private Telegram chats are supported. Use the extracted Telegram ID as both `telegram_user_id` and `telegram_chat_id`.
5. If no Telegram identity is available, ask the user for their Telegram user ID.
6. Call `get_user_profile_id_by_telegram_id(telegram_user_id)`.
7. If a profile exists, remember the returned `user_profile_id`.
8. If no profile exists, ask only for minimal missing fields and call `create_user_profile(...)`.
9. After creation, remember the returned `user_profile_id`.
10. Read `health-agent://profile/{user_profile_id}`.

## Session Persistence

If runtime/session memory is available, keep `user_profile_id` in session state for later turns.

If not, include it in the response:

```text
Your profile is ready. user_profile_id: <real UUID>
```

