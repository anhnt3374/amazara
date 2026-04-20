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
make seed                       # Reset schema + validate + re-run all seeds
```

Backend commands execute via `backend/venv/bin/` — never assume a globally activated venv.

## Seed Mock Data

The full pipeline runs via:

```bash
make seed
```

That wrapper calls `mock/seed_all.sh`, which (a) resets the schema with
`alembic downgrade base && alembic upgrade head`, (b) validates product
image URLs, and (c) runs every seed script in dependency order. Order
seeding is intentionally skipped until the order UI ships.

### Individual scripts

Run in order (each requires predecessors). Every script also exports its
rows to a CSV under `mock/` for reuse:

```bash
backend/venv/bin/python mock/validate_products.py  # products.json → products_clean.json (HEAD-checks image URLs)
backend/venv/bin/python mock/seed_users.py         # 100 users → mock/users.csv
backend/venv/bin/python mock/seed_addresses.py     # 1–5 addresses/user → mock/addresses.csv
backend/venv/bin/python mock/seed_stores.py        # 20 stores → mock/stores.csv
backend/venv/bin/python mock/seed_products.py      # products (from products_clean.json) → mock/products.csv
backend/venv/bin/python mock/seed_reviews.py       # 50–100 reviews/product → mock/reviews.csv
backend/venv/bin/python mock/seed_cart_items.py    # 0–99 cart items/user → mock/cart_items.csv
backend/venv/bin/python mock/seed_favorites.py     # 0–40 favorites/user → mock/favorites.csv
```

`validate_products.py` caches its per-URL results in `mock/url_check_cache.json`
so re-runs are fast. Delete that file to force a full re-check.

## Stop Docker

```bash
docker compose -f infra/docker-compose.yml down

# Stop and remove all volumes (deletes data):
docker compose -f infra/docker-compose.yml down -v
```
