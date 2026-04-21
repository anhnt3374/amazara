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
├── infra/             # docker-compose.yml (MySQL + Milvus)
├── Makefile           # Shortcuts for all common tasks
├── .env.example       # Environment variable template
└── README.md
```

| Directory | Stack | Port |
|---|---|---|
| `frontend/` | React 18, Vite, TypeScript, react-router-dom v6 | 5173 |
| `backend/` | FastAPI, SQLAlchemy ORM, Alembic, python-jose, bcrypt | 8000 |
| `infra/` | MySQL 8.0, Milvus standalone, etcd, MinIO | see below |

## Infrastructure Ports

| Service | Port |
|---|---|
| MySQL | `localhost:3306` |
| Milvus gRPC | `localhost:19530` |
| Milvus HTTP | `localhost:9091` |
| MinIO Console | `localhost:9001` |
| Backend API | `localhost:8000` |
| Frontend dev | `localhost:5173` |

## Dev Proxy

See `docs/features/frontend/conventions.md` — Vite proxies `/api/*` → `:8000` in development.
