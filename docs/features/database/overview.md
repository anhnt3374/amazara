---
feature: database
doc_type: overview
tags: [mysql, milvus, uuid, schema, tables]
---

# Database — Overview

## Engines

| Engine | Purpose | Port |
|---|---|---|
| MySQL 8.0 | Relational data (all 9 tables) | 3306 |
| Milvus | Vector search (future use) | 19530 |

Both started via `make docker-up` (runs `infra/docker-compose.yml`).

## ORM / Migration Stack

- **SQLAlchemy 2.x** — ORM; `SessionLocal` in `backend/app/db/session.py`
- **Alembic** — migration tool; migration files in `backend/alembic/versions/`
- All models registered in `backend/app/db/base.py` for mapper resolution

## Primary Key Convention

All 9 tables use **string UUID primary keys** provided by `UUIDMixin`. UUIDs are auto-generated on insert — no integer sequences.

## Tables

9 tables total:

| Table | Owned by |
|---|---|
| `users` | — |
| `brands` | — |
| `categories` | `brands` |
| `products` | `categories` |
| `orders` | `users` |
| `order_items` | `orders`, `products` |
| `cart_items` | `users`, `products` |
| `addresses` | `users` |
| `reviews` | `users`, `products` |

See `docs/features/database/schema.md` for full FK relationships.
