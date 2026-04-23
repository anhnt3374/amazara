---
doc_type: index
tags: [routing, feature-map, keywords]
---

# Feature Map

Use this file to find the right docs for a given question. Match your keyword to a feature, then read only the listed files.

## auth
**Keywords:** login, register, logout, JWT, token, password, session, me endpoint, get_current_user, AuthContext, useAuth, ProtectedRoute, GuestRoute, localStorage, bearer

| Question type | Read |
|---|---|
| How does auth work overall? | `docs/features/auth/overview.md` |
| What are the API endpoints? | `docs/features/auth/api.md` |
| What is the login/register/logout flow? | `docs/features/auth/flows.md` |
| How does frontend protect routes? | `docs/features/auth/flows.md` |
| How do I call an authenticated endpoint? | `docs/features/auth/api.md` |
| How does password hashing work? | `docs/features/auth/overview.md` |

---

## backend
**Keywords:** FastAPI, endpoint, router, CRUD, SQLAlchemy, model, schema, Pydantic, dependency, Depends, venv, uvicorn, main.py, alembic, migration, store, product, brand, category, order, cart, review

| Question type | Read |
|---|---|
| What are the backend layers? | `docs/features/backend/overview.md` |
| How do I add a new endpoint? | `docs/features/backend/flows.md` |
| How do migrations work? | `docs/features/backend/flows.md` |
| What packages are used? | `docs/features/backend/overview.md` |
| How do I register a new model? | `docs/features/backend/overview.md` |
| Which tables have CRUD/schemas? | `docs/features/backend/overview.md` |

---

## database
**Keywords:** MySQL, Milvus, table, UUID, schema, FK, foreign key, UUIDMixin, alembic/versions, db schema

| Question type | Read |
|---|---|
| What tables exist? | `docs/features/database/overview.md` |
| What are the FK relationships? | `docs/features/database/schema.md` |
| How do I add a table? | `docs/features/database/schema.md` + `docs/features/backend/flows.md` |
| What DB engines are used? | `docs/features/database/overview.md` |
| How do migrations / Alembic work? | `docs/features/backend/flows.md` |

---

## chat
**Keywords:** chat, message, messaging, conversation, websocket, ws, assistant, support, seller chat, store messages, contact seller, unread, notification

| Question type | Read |
|---|---|
| How does chat work overall? | `docs/features/chat/overview.md` |
| What chat endpoints and WS events exist? | `docs/features/chat/api.md` |
| How do user/store/system conversations differ? | `docs/features/chat/overview.md` |
| How are unread counts and read markers handled? | `docs/features/chat/overview.md` + `docs/features/chat/api.md` |
| How do order updates reach the assistant thread? | `docs/features/chat/api.md` |

---

## orders
**Keywords:** order, checkout, place order, order list, order status, shipping, awaiting delivery, completed, cancelled, return, refund, cart to order, buy again, COD, cash on delivery

| Question type | Read |
|---|---|
| How do orders work overall? | `docs/features/orders/overview.md` |
| What are the order API endpoints? | `docs/features/orders/api.md` |
| How does checkout flow from cart to order? | `docs/features/orders/flows.md` |
| Why are "Change" buttons disabled? | `docs/features/orders/flows.md` |
| How do I add a new order status? | `docs/features/orders/flows.md` |

---

## frontend
**Keywords:** React, Vite, TypeScript, Tailwind, component, page, route, Header, Layout, clsx, icon, proxy, form

| Question type | Read |
|---|---|
| What pages/routes exist? | `docs/features/frontend/overview.md` |
| How does the Header work? | `docs/features/frontend/conventions.md` |
| How does Tailwind work here? | `docs/features/frontend/conventions.md` |
| What components exist? | `docs/features/frontend/overview.md` |
| What is the proxy setup? | `docs/features/frontend/conventions.md` |

---

## embedding
**Keywords:** embedding, semantic search, vector search, Milvus, Qwen, fg-clip, multimodal, indexing

| Question type | Read |
|---|---|
| What is the embedding module for? | `docs/features/embedding/overview.md` |
| Which embedding models are supported? | `docs/features/embedding/overview.md` |
| How is a product represented for embeddings? | `docs/features/embedding/overview.md` |
| How will indexing hook into future product uploads? | `docs/features/embedding/overview.md` |

---

## setup / architecture
**Keywords:** install, docker, makefile, .env, port, monorepo, quick start, requirements, seed, mock, csv, json

| Question type | Read |
|---|---|
| How do I set up the project? | `docs/shared/setup.md` |
| What is the overall architecture? | `docs/shared/architecture.md` |
| What are the conventions / rules? | `docs/shared/conventions.md` |
| How do I seed mock data? | `docs/shared/setup.md` |
