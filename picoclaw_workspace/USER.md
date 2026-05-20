# User Context Policy

Do not assume a fixed user. Do not store personal health data in Markdown.

User-specific data must come from current chat/session, explicit user input, MCP tools, or MCP resources backed by SQLite.

## Identity

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal database UUID
```

Rules:

- Never use Telegram ID as `user_profile_id`.
- Never invent UUIDs or placeholders.
- For private Telegram chats, `telegram_user_id == telegram_chat_id`.
- If session metadata contains `direct:<telegram_id>`, use it as both Telegram fields.
- If Telegram ID is not available, ask the user.

## Profile Bootstrap

1. Use `get_user_profile_id_by_telegram_id`.
2. If no profile exists, use `create_user_profile`.
3. Read `health-agent://profile/{user_profile_id}`.
4. Use `user_profile_id` for all domain operations.

After the internal `user_profile_id` is known, keep it in the current session if possible. If not, state it in the chat confirmation so it remains available in conversation history.
