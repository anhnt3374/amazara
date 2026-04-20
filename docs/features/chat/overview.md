---
feature: chat
doc_type: overview
tags: [chat, message, conversation, websocket, bot, langgraph, notification, contact-seller]
---

# Chat — Overview

The chat feature has three participant patterns:

1. **User ↔ Store** — a buyer messages a seller. One conversation per `(user, store)` pair.
2. **User ↔ System** — a buyer chats with a bot-driven "Shope Assistant" thread. One per user.
3. **System notifications** — order lifecycle events (created / status changed / cancelled) are posted as `sender_type='system'` messages into the user's system conversation.

There is **no** user-user or store-store chat. Stores do not receive the floating chat widget, only the `/store/messages` page.

## Scope

- **Transport:** REST for fetching history + WebSocket for real-time delivery.
- **Delivery fan-out:** every new message is broadcast to the user's WS connections and (if present) the store's WS connections via an in-memory `ConnectionManager`.
- **Bot backend:** `BotEngine` is a Strategy interface. The current implementation is `StaticPlaceholderEngine` which returns a fixed string. A future LangGraph engine can be swapped in without touching call-sites — only `get_bot_engine()` changes.
- **Frontend send path:** the frontend sends messages over REST, then relies on WS fan-out for real-time updates and bot/system delivery.
- **Primary UI entry points:** buyer routes are `/messages` and `/messages/:conversationId`; the store route is `/store/messages`; the floating widget opens for guests and users, but only users can enter the messages tab.
- **No chat search, typing indicators, edit/delete, or attachments.**

## Key files

**Backend**

- `backend/app/models/conversation.py` — `Conversation` + `ConversationType` enum (`user_store | user_system`). Unique `(user_id, store_id, type)`.
- `backend/app/models/message.py` — `Message` with `SenderType` (`user | store | bot | system`) and optional `ref_type` / `ref_id` / `ref_payload`.
- `backend/app/schemas/chat.py` — `ConversationOut`, `MessageOut`, `SendMessageRequest`, `WsClientSend`, `WsClientRead`.
- `backend/app/crud/conversation.py` — `get_or_create_user_store`, `get_or_create_user_system`, `list_by_user`, `list_by_store`, `touch_last_message`, `mark_read`, `unread_count`, `is_participant`.
- `backend/app/crud/message.py` — `create_message`, `list_by_conversation`, `last_message`.
- `backend/app/services/chat/bot_engine.py` — `BotEngine` ABC + `StaticPlaceholderEngine` + `get_bot_engine()`.
- `backend/app/services/chat/connection_manager.py` — async in-memory connection registry keyed by `(account_type, account_id)`.
- `backend/app/services/chat/notification_service.py` — `notify_order_created`, `notify_order_status_changed`, `notify_order_cancelled`.
- `backend/app/api/v1/endpoints/chat.py` — REST endpoints under `/api/v1/chats`.
- `backend/app/api/v1/endpoints/chat_ws.py` — WebSocket at `/api/v1/ws/chat?token=...`.
- `backend/alembic/versions/d7e8f1a2b3c4_add_chat_tables.py` — creates `conversations` + `messages`.

**Frontend**

- `frontend/src/types/chat.ts`, `frontend/src/services/chat.ts`.
- `frontend/src/hooks/useChatSocket.ts` — WS lifecycle + auto-reconnect.
- `frontend/src/contexts/ChatContext.tsx` — `ChatProvider` + `useChat` + `useActiveThread`.
- `frontend/src/pages/Messages.tsx` (route `/messages`, `/messages/:conversationId`) — user-side 2-column layout.
- `frontend/src/pages/StoreMessages.tsx` (route `/store/messages`) — store-side 2-column layout.
- `frontend/src/components/ChatWidget.tsx` — floating widget (user/guest only).
- `frontend/src/components/chat/ConversationList.tsx`, `MessageThread.tsx`, `MessageBubble.tsx`, `MessageComposer.tsx`, `ProductRefCard.tsx`, `OrderRefCard.tsx`.

## Data model

**`conversations`**

| column | type | note |
|---|---|---|
| id | CHAR(36) PK | |
| type | ENUM(`user_store`, `user_system`) | |
| user_id | CHAR(36) FK `users.id` | NOT NULL, indexed |
| store_id | CHAR(36) FK `stores.id` | NULL when `type='user_system'`, indexed |
| last_message_at | DATETIME NULL | used to sort the conversation list desc |
| last_read_at_user | DATETIME NULL | unread = messages with `created_at > this` |
| last_read_at_store | DATETIME NULL | NULL for system conversations |
| created_at / updated_at | | `TimestampMixin` |

Unique: `(user_id, store_id, type)`.

**`messages`**

| column | type | note |
|---|---|---|
| id | CHAR(36) PK | |
| conversation_id | CHAR(36) FK `conversations.id` | indexed |
| sender_type | ENUM(`user`, `store`, `bot`, `system`) | |
| sender_id | CHAR(36) NULL | NULL for bot / system |
| content | TEXT | |
| ref_type | ENUM(`product`, `order`, `order_event`) NULL | |
| ref_id | CHAR(36) NULL | product/order id (NULL for `order_event` — payload carries the data) |
| ref_payload | JSON NULL | event snapshot, e.g. `{old,new,order_code,title}` |
| created_at | DATETIME | indexed with `conversation_id` for history paging |

## Statuses & unread

Unread count is derived per viewer:

- User viewing a conversation → `COUNT(messages WHERE created_at > last_read_at_user)`.
- Store viewing → same against `last_read_at_store`.

`POST /chats/{id}/read` (user) or `POST /chats/store/{id}/read` (store) stamps the current time into the relevant column. The WebSocket also accepts `{type:'read', conversation_id}` for the same effect.

At the frontend layer, `ChatContext` also keeps an `unreadTotal` badge for the user widget by summing per-conversation `unread_count`.

## Intentional gaps (not bugs)

- **No chat between two users or two stores.** There is no endpoint, no UI, and no data model for it.
- **Bot replies are synchronous and simple.** `StaticPlaceholderEngine.reply()` returns a fixed string. LangGraph integration is an intentional future extension point.
- **No message history paging UI yet.** `GET /chats/{id}/messages?limit=&before=` supports it; the frontend fetches the latest 100 and does not paginate further.
- **System conversation has no "close"** — it always exists for every user who hits `GET /chats`.
- **WebSocket is not the primary send path in the UI.** The browser keeps the socket open for incoming messages and read events, but outbound messages still go through the REST endpoints.
