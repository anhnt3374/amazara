---
feature: chat
doc_type: api
tags: [chat, api, rest, websocket]
---

# Chat — API Reference

All REST endpoints live under `/api/v1/chats`. All require a Bearer token except the WebSocket, which takes the token in a query param.

## REST

### User-side

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/chats` | user | List the current user's conversations (user-store threads + the system thread; system thread is auto-created if missing). |
| POST | `/chats/system` | user | Get-or-create the user's system conversation. |
| POST | `/chats/with-store/{store_id}` | user | Get-or-create the user-store conversation. |
| GET | `/chats/{conversation_id}/messages?limit=&before=` | user | Load messages (descending, then reversed; paged via `before=<message_id>`). |
| POST | `/chats/{conversation_id}/messages` | user | Send a message as the user. Triggers the configured assistant engine if conversation type is `user_system`. Broadcasts via WS. |
| POST | `/chats/{conversation_id}/assistant-action` | user | Submit a structured assistant action such as confirm-order for the system conversation. |
| POST | `/chats/{conversation_id}/read` | user | Mark the user's last-read timestamp. |

### Store-side

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/chats/store` | store | List the current store's conversations (only `user_store` type). |
| GET | `/chats/store/{conversation_id}/messages?limit=&before=` | store | Load messages. |
| POST | `/chats/store/{conversation_id}/messages` | store | Send a message as the store. Only for `user_store` conversations. |
| POST | `/chats/store/{conversation_id}/read` | store | Mark the store's last-read timestamp. |

### Request / response shapes

`SendMessageRequest`:

```json
{
  "content": "string (required, non-empty after strip)",
  "ref_type": "product | order | order_event | null",
  "ref_id": "uuid | null"
}
```

`MessageOut`:

```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "sender_type": "user | store | bot | system",
  "sender_id": "uuid | null",
  "content": "string",
  "ref_type": "product | order | order_event | null",
  "ref_id": "uuid | null",
  "ref_payload": {"key": "value"} | null,
  "assistant_payload": {"type": "product_carousel"} | null,
  "created_at": "ISO-8601"
}
```

`AssistantActionRequest`:

```json
{
  "action_id": "confirm_order",
  "data": {
    "draft_id": "uuid"
  }
}
```

`ConversationOut`:

```json
{
  "id": "uuid",
  "type": "user_store | user_system",
  "user_id": "uuid",
  "store_id": "uuid | null",
  "partner": {
    "id": "uuid | null",
    "display_name": "string",
    "avatar": "url | null"
  },
  "last_message": MessageOut | null,
  "unread_count": 0,
  "last_message_at": "ISO-8601 | null",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

Authorization: every endpoint checks `is_participant(conv, user_id=... | store_id=...)`. Non-participants get `404`.

## WebSocket

### Connection

`GET /api/v1/ws/chat?token=<jwt>`

- Token is the same JWT issued by auth; it is decoded server-side and matched against the `User` or `Store` row.
- Invalid token → close with code **4401**.
- On connect, the server registers `(account_type, account_id) → set[WebSocket]` in the `ConnectionManager`. Multiple tabs are supported.

### Client → server

```json
{ "type": "send", "conversation_id": "uuid", "content": "string",
  "ref_type": "product | order | order_event | null",
  "ref_id": "uuid | null" }

{ "type": "read", "conversation_id": "uuid" }
```

- `send` persists the message, updates `last_message_at`, and broadcasts to both participants.
- For a `user_system` conversation, after saving the user message the server invokes the configured `BotEngine`. With the default `LangGraphEngine`, messages without digits return a greeting and messages with digits return the sum of all signed integers in the query.

### Server → client

```json
{ "type": "message", "conversation_id": "uuid", "message": MessageOut }
{ "type": "error", "detail": "string" }
```

The same `message` event is also used for:

- A participant receiving the other side's message.
- Echo of your own message (useful when another tab of yours is open).
- Bot replies in the system conversation.
- System notifications triggered by the order endpoints (same channel, `sender_type='system'`).

Errors are soft (sent as a JSON frame, socket stays open) unless auth fails at connect time.

## System assistant runtime

- Default local-safe engine: `BOT_ENGINE=stub`
- Groq engine: `BOT_ENGINE=groq`
- Groq env vars: `GROQ_API_KEY`, `GROQ_MODEL` (default `openai/gpt-oss-120b`), optional `GROQ_BASE_URL`
- Observability env vars: `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
- The Groq runtime returns strict JSON decisions, and backend tool execution turns those decisions into structured assistant payloads such as `product_carousel`, `product_info`, `order_confirmation`, and `order_result`.
- If Groq returns a partial payload with only `product_id`, backend normalization now defaults that response to `view_product` rather than `prepare_order`.

## Order → system notifications

These are posted automatically by `endpoints/order.py` after the corresponding CRUD call succeeds:

| Trigger | Call site | Message shape |
|---|---|---|
| `POST /orders/` | `notify_order_created` | `ref_type='order_event'`, payload `{event:'created', order_id, order_code, title}` |
| `PATCH /orders/{id}/status` | `notify_order_status_changed` | `ref_type='order_event'`, payload `{event:'status_changed', old, new, order_id, order_code, title}` |
| `POST /orders/{id}/cancel` | `notify_order_cancelled` | `ref_type='order_event'`, payload `{event:'cancelled', order_id, order_code, title}` |

The system conversation is get-or-created inside the notification service, so the user does not need to open `/messages` first to receive them.
