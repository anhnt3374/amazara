---
doc_type: architecture
tags: [monorepo, layout, services, cloud]
---

# Architecture Overview

## Monorepo Layout

```
Amaraza/
├── frontend/          # React 18 + Vite + TypeScript
├── backend/           # Python + FastAPI + SQLAlchemy + Alembic
├── mock/              # Seed scripts + CSV/JSON data
├── docs/              # Feature docs, indexes, shared conventions
├── Makefile           # Shortcuts for all common tasks
├── .env.example       # Environment variable template (cloud creds)
└── README.md
```

| Directory | Stack | Port |
|---|---|---|
| `frontend/` | React 18, Vite, TypeScript, react-router-dom v6 | 5173 |
| `backend/` | FastAPI, SQLAlchemy ORM, Alembic, python-jose, bcrypt | 8000 |

## Cloud services (no Docker required)

This branch runs entirely against managed cloud services. Connection
strings live in `backend/.env` (see `.env.example`).

| Service | Provider | Used for |
|---|---|---|
| PostgreSQL 16 | Supabase | All relational data (10 tables) |
| Weaviate (vector DB) | Weaviate Cloud | Semantic-search vectors (HNSW + cosine) |
| Redis | Upstash / Redis Cloud | Search result cache (TLS via `rediss://`) |

Local services run on:

| Service | Port |
|---|---|
| Backend API | `localhost:8000` |
| Frontend dev | `localhost:5173` |

## Dev Proxy

See `docs/features/frontend/conventions.md` — Vite proxies `/api/*` → `:8000` in development.
