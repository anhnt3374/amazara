---
feature: backend
doc_type: overview
tags: [fastapi, sqlalchemy, layers, structure, crud]
---

# Backend — Overview

## Stack

FastAPI + SQLAlchemy ORM + Alembic + python-jose + bcrypt. All source code under `backend/app/`.

## Layer Structure

| Layer | Path | Responsibility |
|---|---|---|
| Entry point | `main.py` | Imports `app.db.base` first (registers all ORM models); creates FastAPI app, CORS (allows `localhost:5173`), mounts `api_router` |
| Config | `core/config.py` | Pydantic `Settings` reads `backend/.env`; exposes `settings` singleton and `settings.DATABASE_URL` |
| Security | `core/security.py` | Password hashing via `bcrypt` (SHA-256 pre-hash); JWT encode/decode via `python-jose` |
| DB session | `db/session.py` | SQLAlchemy `engine` + `SessionLocal`; `get_db()` FastAPI dependency |
| Model registry | `db/base.py` | Imports all models — **must be updated** when adding a new model |
| Models | `models/` | One file per table; all inherit `Base` + `UUIDMixin` |
| Schemas | `schemas/` | Pydantic v2 models for request/response validation |
| CRUD | `crud/` | Plain functions accepting `Session`; no repository class pattern |
| API | `api/v1/endpoints/` | FastAPI routers; mounted via `api/v1/router.py` at prefix `/api/v1` |

## CRUD & Schema Coverage

All 10 tables have both CRUD (`crud/`) and schema (`schemas/`) modules:

| Entity | CRUD | Schema | API Router |
|---|---|---|---|
| user | `crud/user.py` | `schemas/user.py` | `endpoints/auth.py` |
| address | `crud/address.py` | `schemas/address.py` | `endpoints/address.py` |
| store | `crud/store.py` | `schemas/store.py` | — |
| brand | `crud/brand.py` | `schemas/brand.py` | — |
| category | `crud/category.py` | `schemas/category.py` | — |
| product | `crud/product.py` | `schemas/product.py` | — |
| order | `crud/order.py` | `schemas/order.py` | — |
| cart_item | `crud/cart_item.py` | `schemas/cart_item.py` | — |
| review | `crud/review.py` | `schemas/review.py` | — |

Schema naming: `{Model}Create`, `{Model}Update` (all fields optional), `{Model}Out` (with `from_attributes`).

CRUD naming: `create_{model}`, `get_{model}_by_id`, `get_{models}_by_{field}`, `update_{model}`, `delete_{model}`.

## Key Rules

- `main.py` **must** import `app.db.base` before anything that uses ORM models — ensures mapper resolution before the first request
- Every new model file **must** be imported in `db/base.py`
- CRUD layer: plain functions only, no class-based repositories
- All routers registered in `api/v1/router.py`

## Dependencies

See `backend/requirements.txt`. Key packages:

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `sqlalchemy` | ORM |
| `alembic` | DB migrations |
| `pymysql` | MySQL driver |
| `python-jose[cryptography]` | JWT |
| `bcrypt` | Password hashing |
| `pydantic-settings` | Config from `.env` |
| `pydantic[email]` | Request/response validation |
