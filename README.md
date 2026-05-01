# Amaraza

E-commerce monorepo with **Frontend** (React + Vite + TypeScript), **Backend** (FastAPI + SQLAlchemy), and **cloud-only data plane** — Supabase Postgres, Weaviate Cloud, Redis Cloud.

## Project Structure

```
Amaraza/
├── frontend/          # React + Vite + TypeScript
├── backend/           # Python + FastAPI + SQLAlchemy + Alembic
├── mock/              # Seed scripts + CSV/JSON data
├── docs/              # Feature docs, indexes, shared conventions
├── Makefile           # Shortcuts for common tasks
├── .env.example       # Environment variable template
└── README.md
```

## Quick Start (via Makefile)

```bash
cp .env.example backend/.env   # 1. Fill in cloud credentials (see Step 1)
make venv                      # 2a. Create virtual environment
make install-backend           # 2b. Install Python packages
make install-ml-cu128          # 2c. (or install-ml-cu126 / install-ml-cpu) install ML deps
make migrate                   # 3. Apply migrations to Supabase Postgres
make seed                      # 4. (Optional) seed mock data
make reindex                   # 5. (Optional) build Weaviate Cloud index
make run-backend               # 6. Run API server
# In another terminal:
make install-frontend          # 7. Install Node packages
make run-frontend              # 8. Run Vite dev server
```

See all available commands: `make help`

---

## Requirements

| Tool | Minimum version | Why |
|---|---|---|
| Python | 3.13 (3.13.12 tested) | Backend runtime |
| Node.js | 20+ | Vite frontend |
| NVIDIA GPU + CUDA 12.6 / 12.8 | optional | Faster image embedding (`install-ml-cu126` for RTX 30/40 / A100, `install-ml-cu128` for RTX 50-series / Blackwell). CPU fallback works. |

This branch does **not** require Docker. All data services are managed cloud:

| Service | Provider (recommended) | What you get |
|---|---|---|
| PostgreSQL 16 | [Supabase](https://supabase.com) free tier | 500 MB, direct + pooled connections |
| Weaviate (vector DB) | [Weaviate Cloud](https://console.weaviate.cloud) sandbox | 2-week free sandbox or paid serverless |
| Redis | [Upstash](https://upstash.com) free tier | 10 K cmd/day, TLS, `rediss://` URL |

---

## Step 1 — Configure `.env`

```bash
cp .env.example backend/.env
```

Open `backend/.env` and fill in:

```env
# Supabase: Settings → Database → Connection string (Direct)
POSTGRES_HOST=db.<project-ref>.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your supabase db password>
POSTGRES_DATABASE=postgres

# Weaviate Cloud dashboard: copy the REST URL (without https://) and admin API key
WEAVIATE_URL=<cluster-id>.<region>.gcp.weaviate.cloud
WEAVIATE_API_KEY=<your weaviate admin key>

# Upstash / Redis Cloud: copy the rediss:// connection string
REDIS_URL=rediss://default:<password>@<host>:<port>

# JWT
SECRET_KEY=<strong random string — see below>

# Chat
GROQ_API_KEY=<your groq api key>
```

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 2 — Install Backend

```bash
make venv
make install-backend
make install-ml-cu128   # RTX 50-series, H100, Blackwell (CUDA 12.8)
make install-ml-cu126   # RTX 30/40, A100, V100 (CUDA 12.6)
make install-ml-cpu     # CPU-only fallback
```

ML deps include `torch`, `transformers`, `sentence-transformers`, `weaviate-client`, `redis`. The embedders (BGE + FG-CLIP 2) auto-detect GPU via `SEMANTIC_DEVICE=auto`.

---

## Step 3 — Run Database Migrations

```bash
make migrate
```

This creates all 10 tables in your Supabase Postgres:
`users`, `stores`, `brands`, `categories`, `products`, `orders`, `order_items`, `cart_items`, `addresses`, `reviews` (plus chat tables).

Verify in Supabase dashboard → Table Editor.

To generate a new migration after changing a model:

```bash
make makemigrations msg="describe your change"
make migrate
```

---

## Step 4 — (Optional) Seed Mock Data

```bash
make seed   # full pipeline: reset schema + validate + seed all
```

Or run individual scripts under `mock/` (they are DB-agnostic and use the SQLAlchemy ORM, so they connect to Supabase via `DATABASE_URL`).

---

## Step 5 — (Optional) Build Weaviate Cloud Vector Index

```bash
make reindex
```

This calls `backend/scripts/reindex_products.py` which:

1. Loads every Product row from Supabase Postgres.
2. Encodes descriptions with **BGE-small-en-v1.5** (384-dim) and images with **FG-CLIP 2** (768-dim).
3. Upserts into two Weaviate Cloud collections — `ProductImageVecV1` (one object per image) and `ProductDescVecV1` (one per product).

First run downloads model weights (~600 MB FG-CLIP 2 + ~130 MB BGE) and uploads vectors over the network.

---

## Step 6 — Run Backend

```bash
make run-backend
```

- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### API Endpoints (subset)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new account |
| POST | `/api/v1/auth/login` | Log in and receive a JWT token |
| POST | `/api/v1/auth/logout` | Log out (client discards token) |
| GET  | `/api/v1/auth/me` | Get current user info (Bearer token required) |
| CRUD | `/api/v1/addresses` | User addresses |
| GET  | `/api/v1/products/search?search=...` | Semantic search (Weaviate Cloud) |

---

## Step 7 — Install & Run Frontend

```bash
make install-frontend
make run-frontend
```

Frontend runs at: http://localhost:5173

Vite is configured with a proxy: all requests to `/api/*` are forwarded to `http://localhost:8000`.

---

## Smoke Test

With backend and frontend running, verify the main flows with:

```bash
backend/venv/bin/python backend/scripts/smoke_test.py
```

The script prints a JSON summary and cleans up the generated `smoke.*` data automatically.
