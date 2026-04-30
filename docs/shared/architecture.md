---
doc_type: architecture
tags: [monorepo, layout, services, ports]
---

# Architecture Overview

## Monorepo Layout

```
Amaraza/
├── frontend/          # React 18 + Vite + TypeScript
├── backend/           # Python + FastAPI + SQLAlchemy + Alembic
├── infra/             # docker-compose.yml (PostgreSQL + Weaviate)
├── Makefile           # Shortcuts for all common tasks
├── .env.example       # Environment variable template
└── README.md
```

| Directory | Stack | Port |
|---|---|---|
| `frontend/` | React 18, Vite, TypeScript, react-router-dom v6 | 5173 |
| `backend/` | FastAPI, SQLAlchemy ORM, Alembic, python-jose, bcrypt | 8000 |
| `infra/` | PostgreSQL 16, Weaviate, Redis | see below |

## Infrastructure Ports

| Service | Port |
|---|---|
| PostgreSQL | `localhost:5432` |
| Weaviate HTTP | `localhost:8080` |
| Weaviate gRPC | `localhost:50051` |
| Redis | `localhost:6379` |
| Backend API | `localhost:8000` |
| Frontend dev | `localhost:5173` |

## Dev Proxy

See `docs/features/frontend/conventions.md` — Vite proxies `/api/*` → `:8000` in development.
