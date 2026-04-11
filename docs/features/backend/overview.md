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
