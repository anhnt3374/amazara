---
doc_type: setup
tags: [install, env, cloud, supabase, weaviate, upstash, quickstart, makefile, ml, semantic-search, embedding, reindex]
---

# Project Setup

End-to-end guide: provision cloud services → clone → install → migrate
schema → seed mock data → build vector index → run backend + frontend →
verify. Follow top-to-bottom for a fresh machine.

This branch uses **cloud-only** data services. There is no `docker-compose`
to bring up; you provision Supabase, Weaviate Cloud, and a Redis provider
once and reuse them.

## 1. Requirements

| Tool | Required version | Why |
|---|---|---|
| Python | **3.13** (3.13.12 tested) | Backend runtime; pyenv recommended |
| Node.js | 20+ | Vite frontend |
| NVIDIA GPU + CUDA 12.6 / 12.8 | optional | Faster image embedding (`install-ml-cu126` for older GPUs, `install-ml-cu128` for RTX 50-series / Blackwell) |
| Disk | ~2 GB free | torch + FG-CLIP 2 weights cached locally |
| RAM | 4 GB+ | Embedders only — no local DB to host |

## 2. Provision cloud services (one-time)

| Service | Where | Free tier? | What to copy |
|---|---|---|---|
| **Supabase Postgres** | <https://supabase.com> → New project | 500 MB | Settings → Database → Connection string (Direct, port 5432) |
| **Weaviate Cloud** | <https://console.weaviate.cloud> → Create cluster | 14-day sandbox | Cluster details → REST endpoint URL + Admin API key |
| **Upstash Redis** (or Redis Cloud) | <https://upstash.com> → Create database | 10 K cmd/day | Database details → Redis URL (`rediss://...`) |

Pick a region close to your backend host for Weaviate and Supabase
(latency on the ANN search path is dominated by network).

## 3. Clone + Python venv

```bash
git clone <repo-url> shope
cd shope

# Create Python 3.13 venv (do NOT use system `python` — may default to 3.12)
/home/<you>/.pyenv/versions/3.13.12/bin/python -m venv backend/venv
# Or, on systems with `python3.13` on PATH:
# python3.13 -m venv backend/venv

backend/venv/bin/python --version    # → Python 3.13.12
```

## 4. Configure environment

```bash
cp .env.example backend/.env
```

Open `backend/.env` and paste the credentials you collected in step 2:

| Key | Where to get it |
|---|---|
| `POSTGRES_HOST/PORT/USER/PASSWORD/DATABASE` | Supabase → Database connection string |
| `WEAVIATE_URL` | Weaviate Cloud cluster details (REST URL, no `https://`) |
| `WEAVIATE_API_KEY` | Weaviate Cloud → API keys → Admin |
| `REDIS_URL` | Upstash / Redis Cloud connection URL (use `rediss://` for TLS) |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GROQ_API_KEY` | <https://console.groq.com> (only if `BOT_ENGINE=groq`) |

Semantic-search defaults are already in `.env.example`; useful tuning knobs:

| Key | Default | Effect |
|---|---|---|
| `SEMANTIC_FUSION_ALPHA` | `0.8` | Weight of image side in score fusion (text = 1−α) |
| `SEMANTIC_OUTLIER_RATIO_TAU` | `0.6` | Drop items below `τ × top1` |
| `SEMANTIC_IMAGE_AGG_TOP_K` | `3` | Mean of K best images per product |
| `SEMANTIC_DEVICE` | `auto` | `auto` / `cuda` / `cpu` |
| `SEMANTIC_CACHE_BACKEND` | `redis` | `redis` (multi-worker) or `memory` (single) |

## 5. Install dependencies

### 5a. Backend base packages

```bash
make install-backend
# = pip install -r backend/requirements-base.txt (FastAPI, SQLAlchemy, psycopg, …)
```

### 5b. ML stack (torch + transformers + weaviate-client + redis)

Pick **one** based on hardware:

```bash
# RTX 50-series, H100, Blackwell (CUDA 12.8)
make install-ml-cu128

# RTX 30/40, A100, V100 (CUDA 12.6)
make install-ml-cu126

# CPU-only fallback
make install-ml-cpu
```

These targets pull `torch==2.7.1+{cu128,cu126,cpu}` and
`torchvision==0.22.1+{cu128,cu126,cpu}` from `download.pytorch.org`, then
install the rest of `backend/requirements-ml.txt`
(transformers, sentence-transformers, weaviate-client, redis, etc.).

> **Why those pins:** FG-CLIP 2 (`qihoo360/fg-clip2-base`) needs
> `transformers ≥ 4.50`, which pairs with torch ≥ 2.7. Embedders use
> `SEMANTIC_DEVICE=auto` to detect CUDA at runtime.

### 5c. Frontend packages

```bash
make install-frontend
```

### 5d. ML stack smoke test

```bash
make check-ml-env
```

Expected: prints torch/transformers/weaviate versions, then `OK` after
loading BGE and running one forward pass. First run downloads BGE
weights (~130 MB) into `~/.cache/huggingface`.

## 6. Apply database migrations

```bash
make migrate
```

This runs `alembic upgrade head` against your **Supabase** Postgres,
creating the 10 tables (`users`, `stores`, `brands`, `categories`,
`products`, `orders`, `order_items`, `cart_items`, `addresses`,
`reviews`) plus chat tables. Verify in Supabase dashboard → Table
Editor.

To generate a new migration after a model change:

```bash
make makemigrations msg="describe your change"
make migrate
```

## 7. Seed mock data (optional)

```bash
make seed
```

Calls `mock/seed_all.sh`:

1. `alembic downgrade base && alembic upgrade head` — clean schema
2. Validates 1000+ product image URLs (cached in `mock/url_check_cache.json`)
3. Seeds 100 users, addresses, 20 stores, products, reviews, carts, favorites

Each script is idempotent and writes a CSV under `mock/` for reuse.

## 8. Build the semantic-search vector index

```bash
make reindex
```

Calls `backend/scripts/reindex_products.py`:

1. Loads every Product row from Supabase Postgres.
2. Splits image URLs (pipe-separated `|`), keeps the first
   `SEMANTIC_MAX_IMAGES_PER_PRODUCT` (default 4) per product.
3. Concurrently fetches images via aiohttp.
4. Embeds descriptions with **BGE-small-en-v1.5** (384-dim) and images
   with **FG-CLIP 2** (`qihoo360/fg-clip2-base`, 768-dim).
5. Upserts into two **Weaviate Cloud** collections:
   - `ProductImageVecV1` — one object per image
   - `ProductDescVecV1` — one object per product description
6. Clears the search cache.

First run downloads model weights and uploads vectors over the network.
Subsequent runs reuse cached weights; use `--product-ids` for partial
re-index.

### Common reindex flags

```bash
backend/venv/bin/python backend/scripts/reindex_products.py --rebuild
backend/venv/bin/python backend/scripts/reindex_products.py --product-ids "id1,id2"
backend/venv/bin/python backend/scripts/reindex_products.py --skip-images
backend/venv/bin/python backend/scripts/reindex_products.py --skip-descriptions
backend/venv/bin/python backend/scripts/reindex_products.py \
    --batch-size-products 32 --image-batch-size 16
```

## 9. Run the application

```bash
# Terminal 1 — FastAPI
make run-backend       # http://localhost:8000

# Terminal 2 — Vite
make run-frontend      # http://localhost:5173
```

The frontend dev server proxies API calls to `:8000`.

## 10. Verify end to end

### Backend health

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Semantic search

```bash
curl 'http://localhost:8000/products/search?search=running+shoes&page=1' | head -c 600
```

Expected: JSON `ProductSearchResponse` with `products` ranked by
relevance and `available_brands` / `available_categories` reflecting
the candidate set after outlier cut. The second identical call should
return in <50 ms (Redis cache hit).

### Lexical-only fallback (no query)

```bash
curl 'http://localhost:8000/products/search?page=1' | head -c 600
```

Skips Weaviate entirely and returns the first page of all products.

### Smoke test (full system)

```bash
backend/venv/bin/python backend/scripts/smoke_test.py
```

## 11. Common operations

### Re-tune ranking without reindexing

Change any `SEMANTIC_*` query/cache parameter in `backend/.env` and
restart the backend. No reindex needed for: `SEMANTIC_FUSION_ALPHA`,
`SEMANTIC_OUTLIER_RATIO_TAU`, `SEMANTIC_IMAGE_AGG_TOP_K`,
`SEMANTIC_ANN_TOPN_*`, `SEMANTIC_CACHE_*`.

### Swap models or change collection schema

Bump the collection name to `_v2` in `.env` and run `make reindex --rebuild`
into the new namespace. When ready, swap `SEMANTIC_COLLECTION_*` and
restart the backend (zero-downtime cutover).

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python -m venv` makes 3.12 venv | pyenv shim points at 3.12 | Use full path `~/.pyenv/versions/3.13.12/bin/python` |
| `pip install torch==2.7.1+cuXYZ` cannot find version | Wrong index URL | Match the index URL to the wheel suffix: `whl/cu126` for `+cu126`, `whl/cu128` for `+cu128`, `whl/cpu` for `+cpu`. |
| `psycopg.OperationalError: SSL connection required` | Supabase requires TLS | App appends `?sslmode=require` automatically — confirm `psycopg[binary]>=3.2` is installed |
| `weaviate.exceptions.UnexpectedStatusCodeError: 401` | Wrong API key / cluster URL | Check `WEAVIATE_API_KEY` is the *Admin* key and `WEAVIATE_URL` has no `https://` prefix |
| `redis.exceptions.AuthenticationError` | Wrong Redis URL | Use the full `rediss://default:<pwd>@host:port` string from your provider |
| `Unrecognized configuration class Fgclip2Config for AutoModel` | Old transformers | Re-run an `install-ml-*` target to pull `transformers>=4.56`. |
| Endpoint returns 503 "semantic search temporarily unavailable" | Weaviate Cloud unreachable or model load failure | Check Weaviate dashboard; check backend logs for embedder load error |
| `make reindex` slow on first run | Downloading weights + network upload | Expected; subsequent runs are faster |

## All Makefile commands

```
Backend
  make venv                  Create virtual environment at backend/venv
  make install-backend       Install Python packages
  make makemigrations msg=x  Generate Alembic migration file from models
  make migrate               Apply pending migrations to Supabase Postgres
  make run-backend           Run FastAPI dev server (port 8000)

Semantic Search
  make install-ml-cpu        Install PyTorch (CPU) and ML deps
  make install-ml-cu126      Install PyTorch (CUDA 12.6) and ML deps — RTX 30/40, A100, V100
  make install-ml-cu128      Install PyTorch (CUDA 12.8) and ML deps — RTX 50-series, H100, Blackwell
  make check-ml-env          Smoke-test ML stack (loads BGE encoder)
  make reindex               Rebuild Weaviate Cloud collections from Supabase products

Frontend
  make install-frontend      Install Node packages (npm install)
  make run-frontend          Run Vite dev server (port 5173)

Data
  make seed                  Reset schema + validate + re-run all seeds
```

Backend commands execute via `backend/venv/bin/` — never assume a globally
activated venv.
