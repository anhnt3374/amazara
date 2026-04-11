---
doc_type: setup
tags: [install, env, docker, quickstart, makefile]
---

# Project Setup

## Requirements

| Tool | Minimum version |
|---|---|
| Docker + Docker Compose | 24.x |
| Python | 3.11+ |
| Node.js | 20+ |

## Quick Start

```bash
cp .env.example backend/.env   # 1. Configure env
make docker-up                 # 2. Start MySQL + Milvus
make venv                      # 3a. Create Python venv
make install-backend           # 3b. Install Python packages
make migrate                   # 4. Create DB tables
make run-backend               # 5. Start API server (:8000)
# In another terminal:
make install-frontend          # 6. Install Node packages
make run-frontend              # 7. Start Vite dev server (:5173)
```

## Environment Variables

Copy and edit:
```bash
cp .env.example backend/.env
```

Key variables in `backend/.env`:
```env
MYSQL_PASSWORD=shope_password
SECRET_KEY=<strong random string>
```

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`backend/.env` is loaded by `backend/app/core/config.py` via Pydantic `Settings`.

## All Makefile Commands

```bash
make venv                       # Create backend/venv
make install-backend            # pip install -r backend/requirements.txt into venv
make makemigrations msg=<name>  # Generate Alembic migration file
make migrate                    # Apply pending migrations (alembic upgrade head)
make run-backend                # uvicorn on :8000 with --reload
make install-frontend           # npm install in frontend/
make run-frontend               # Vite dev server on :5173
make docker-up                  # Start MySQL + Milvus
make docker-down                # Stop Docker services
```

Backend commands execute via `backend/venv/bin/` — never assume a globally activated venv.

## Stop Docker

```bash
docker compose -f infra/docker-compose.yml down

# Stop and remove all volumes (deletes data):
docker compose -f infra/docker-compose.yml down -v
```
