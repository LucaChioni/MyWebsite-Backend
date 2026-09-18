# Personal Website - Backend

Backend repository for my [Personal Website](https://lucachioni.com/).

## Stack

- Uvicorn
- Python
- FastAPI

## Chat

`POST /api/chat` returns `{"reply": ..., "conversation_id": ...}` from Claude (`claude-haiku-4-5`) impersonating me, using `data/about_me.md` as its only knowledge.

The Anthropic API key is read from the `app_settings` table (created by `migrations/migration_002.sql`):

```sql
INSERT INTO app_settings (key, value) VALUES ('anthropic_api_key', 'sk-ant-...')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
```

The key is cached in memory after the first request; restart the backend after changing it.

Every question and reply is stored in `chat_messages`, which references `chat_conversations` through `conversation_id` (`migrations/migration_003.sql`). The server creates the conversation on the first message and the browser sends its id back with the following ones (a page reload starts a new conversation).
