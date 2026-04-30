---
feature: database
doc_type: overview
tags: [postgresql, weaviate, uuid, schema, tables]
---

# Database — Overview

## Engines

| Engine | Provider | Purpose | Connection |
|---|---|---|---|
| PostgreSQL 16 | Supabase (managed) | Relational data (all 9 tables) | `POSTGRES_*` env vars; SSL enforced |
| Weaviate | Weaviate Cloud (managed) | Vector search (semantic-search feature) | `WEAVIATE_URL` + `WEAVIATE_API_KEY` |

Both are cloud-only; no local Docker. See `docs/shared/setup.md` for how
to provision and configure them.

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
