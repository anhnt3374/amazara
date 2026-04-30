---
doc_type: setup
tags: [install, env, docker, quickstart, makefile, ml, semantic-search, embedding, reindex]
---

# Project Setup

End-to-end guide: clone → install → seed mock data → build vector index →
run backend + frontend → verify. Follow top-to-bottom for a fresh machine.

## 1. Requirements

| Tool | Required version | Why |
|---|---|---|
| Docker + Docker Compose | 24.x+ | PostgreSQL, Weaviate, Redis containers |
| Python | **3.13** (3.13.12 tested) | Production runtime; pyenv recommended |
| Node.js | 20+ | Vite frontend |
| Disk | ~6 GB free | torch + FG-CLIP 2 weights + Weaviate data |
| RAM | 8 GB+ | Weaviate uses ~500 MB idle; embedders share rest |

GPU is optional. Everything below works on CPU; ML index build is just slower.

## 2. Clone + Python venv

```bash
git clone <repo-url> shope
cd shope

# Create Python 3.13 venv (do NOT use system `python` — may default to 3.12)
/home/<you>/.pyenv/versions/3.13.12/bin/python -m venv backend/venv
# Or, on systems with `python3.13` on PATH:
# python3.13 -m venv backend/venv

# Verify
backend/venv/bin/python --version    # → Python 3.13.12
```

## 3. Configure environment

```bash
cp .env.example backend/.env
```

Edit `backend/.env`. Required values:

| Key | Example | Note |
|---|---|---|
| `POSTGRES_PASSWORD` | `shope_password` | Match docker-compose default or override |
| `SECRET_KEY` | `<random>` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GROQ_API_KEY` | `gsk_...` | Required only if `BOT_ENGINE=groq` |

Semantic-search defaults are already in `.env.example` and rarely need
changes. The most useful tuning knobs:

| Key | Default | Effect |
|---|---|---|
| `SEMANTIC_FUSION_ALPHA` | `0.5` | Weight of image side in score fusion (text = 1−α) |
| `SEMANTIC_OUTLIER_RATIO_TAU` | `0.6` | Drop items below `τ × top1` |
| `SEMANTIC_IMAGE_AGG_TOP_K` | `3` | Mean of K best images per product |
| `SEMANTIC_DEVICE` | `auto` | `auto` / `cuda` / `cpu` |
| `SEMANTIC_CACHE_BACKEND` | `memory` | `memory` (dev) or `redis` (multi-worker) |

## 4. Install dependencies

### 4a. Backend base packages

```bash
backend/venv/bin/pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements-base.txt
```

### 4b. ML stack (torch + transformers + weaviate-client + redis client)

Pick **one** based on hardware:

```bash
# CPU-only (dev machine without NVIDIA GPU)
make install-ml-cpu

# CUDA 12.4 (production GPU)
make install-ml-gpu
```

These targets pull `torch==2.11.0+{cpu,cu124}` and
`torchvision==0.26.0+{cpu,cu124}` from `download.pytorch.org`, then install
the rest of `backend/requirements-ml.txt` (transformers, sentence-transformers,
weaviate-client, redis, etc.).

> **Why those pins:** FG-CLIP 2 (`qihoo360/fg-clip2-base`) needs
> `transformers ≥ 4.50` (uses `transformers.modeling_layers`), which in
> turn pairs with torch ≥ 2.7. torch 2.11.0 + torchvision 0.26.0 are the
> latest stable cp313 wheels. `transformers` is pinned `>=4.56,<5`.
> Don't substitute the CPU/GPU index — PyPI's default torch wheels are
> CUDA-flavored and large.

### 4c. Frontend packages

```bash
make install-frontend
```

### 4d. ML stack smoke test

```bash
make check-ml-env
```

Expected: prints torch/transformers/weaviate versions, then `OK` after
loading BGE and running one forward pass. First run downloads BGE
weights (~130 MB) into `~/.cache/huggingface`.

## 5. Boot Docker services

```bash
make docker-up
```

Brings up three containers: PostgreSQL 16, Weaviate 1.37.x, and Redis 7.
Wait until they report healthy:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output (after ~15 s):

```
NAMES             STATUS
shope_postgres    Up (healthy)
shope_weaviate    Up
shope_redis       Up (healthy)
```

## 6. Database migrations + seed data

```bash
# Apply Alembic migrations to create the 9 PostgreSQL tables
make migrate

# Reset schema + run every seed script in dependency order
make seed
```

`make seed` calls `mock/seed_all.sh`, which:

1. `alembic downgrade base && alembic upgrade head` — clean schema
2. Validates 1000+ product image URLs (cached in `mock/url_check_cache.json`)
3. Seeds 100 users, addresses, 20 stores, products, reviews, carts, favorites

Run individual scripts if you need partial reseeding:

```bash
backend/venv/bin/python mock/validate_products.py
backend/venv/bin/python mock/seed_users.py
backend/venv/bin/python mock/seed_addresses.py
backend/venv/bin/python mock/seed_stores.py
backend/venv/bin/python mock/seed_products.py
backend/venv/bin/python mock/seed_reviews.py
backend/venv/bin/python mock/seed_cart_items.py
backend/venv/bin/python mock/seed_favorites.py
```

Each script writes a CSV under `mock/` for reuse and is idempotent given
the same inputs.

## 7. Build the semantic-search vector index

```bash
make reindex
```

This calls `backend/scripts/reindex_products.py` which:

1. Loads every Product row from PostgreSQL.
2. Splits image URLs (pipe-separated `|`), keeps the first
   `SEMANTIC_MAX_IMAGES_PER_PRODUCT` (default 4) per product.
3. Concurrently fetches images via aiohttp.
4. Embeds descriptions with **BGE-small-en-v1.5** (384-dim) and images with
   **FG-CLIP 2** (`qihoo360/fg-clip2-base`, 768-dim).
5. Upserts into two Weaviate collections:
   - `ProductImageVecV1` — one object per image
   - `ProductDescVecV1` — one object per product description
6. Clears the search cache.

First run downloads model weights (~600 MB FG-CLIP 2 + ~130 MB BGE) and
takes a long time on CPU (~minutes per 100 products). Subsequent runs
are faster (cached weights, can use `--product-ids` for partial updates).

### Common reindex flags

```bash
# Rebuild from scratch (drop + recreate Weaviate collections)
backend/venv/bin/python backend/scripts/reindex_products.py --rebuild

# Reindex a subset only
backend/venv/bin/python backend/scripts/reindex_products.py \
    --product-ids "id1,id2,id3"

# Skip a modality for faster iteration
backend/venv/bin/python backend/scripts/reindex_products.py --skip-images
backend/venv/bin/python backend/scripts/reindex_products.py --skip-descriptions

# Tune batch sizes
backend/venv/bin/python backend/scripts/reindex_products.py \
    --batch-size-products 32 --image-batch-size 16
```

The script logs progress every 100 products. Image fetch failures are
logged and skipped — products without any successful image still get
indexed with a description-only embedding.

## 8. Run the application

```bash
# Terminal 1 — FastAPI
make run-backend       # http://localhost:8000

# Terminal 2 — Vite
make run-frontend      # http://localhost:5173
```

The frontend dev server proxies API calls to `:8000`.

## 9. Verify end to end

### Backend health

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Semantic search

```bash
curl 'http://localhost:8000/products/search?search=running+shoes&page=1' | head -c 600
```

Expected: JSON `ProductSearchResponse` with `products` ranked by relevance,
`total > 0`, and `available_brands` / `available_categories` reflecting the
candidate set after outlier cut. The second identical call should return
in <50 ms (cache hit).

### Lexical-only fallback (no query)

```bash
curl 'http://localhost:8000/products/search?page=1' | head -c 600
```

This skips Weaviate entirely and returns the first page of all products.

### Smoke test (full system)

```bash
backend/venv/bin/python backend/scripts/smoke_test.py
```

Covers backend health, frontend routes, auth, product search, addresses,
favorites, cart, orders, REST + WebSocket chat. Prints
`PASS` / `FAIL` / `BLOCKED` per check and cleans up its own
`smoke.*` test data.

```bash
backend/venv/bin/python backend/scripts/smoke_test.py --keep-data
backend/venv/bin/python backend/scripts/smoke_test.py --cleanup-only
```

## 10. Common operations

### Re-tune ranking without reindexing

Change any `SEMANTIC_*` query/cache parameter in `backend/.env` and
restart the backend. No reindex needed for: `SEMANTIC_FUSION_ALPHA`,
`SEMANTIC_OUTLIER_RATIO_TAU`, `SEMANTIC_IMAGE_AGG_TOP_K`,
`SEMANTIC_ANN_TOPN_*`, `SEMANTIC_CACHE_*`.

### Switch cache to Redis

```bash
# In backend/.env
SEMANTIC_CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

Restart backend. Redis is already in docker-compose.

### Swap models or change collection schema

Bump the collection name to `_v2` in `.env` and run `make reindex --rebuild`
in the new namespace. When ready, swap `SEMANTIC_COLLECTION_*` settings
and restart the backend (zero-downtime cutover).

### Stop services

```bash
make docker-down                # Stop containers, keep volumes
docker compose -f infra/docker-compose.yml down -v   # Also drop all data
```

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python -m venv` makes 3.12 venv | pyenv shim points at 3.12 | Use full path `~/.pyenv/versions/3.13.12/bin/python` |
| `pip install torch==2.11.0+cpu` cannot find version | Wrong index URL | Ensure `--index-url https://download.pytorch.org/whl/cpu` |
| `Unrecognized configuration class Fgclip2Config for AutoModel` | Used `AutoModel` instead of `AutoModelForCausalLM` | Already fixed in `embedders/fgclip.py` — pull latest |
| `weaviate-client` import fails | Mismatched client version | `requirements-ml.txt` pins `weaviate-client>=4.9,<5`; reinstall |
| `EmbedderUnavailable: FG-CLIP 2 load failed` | Wrong transformers version | `make install-ml-cpu` again to pull `transformers>=4.56` |
| Endpoint returns 503 "semantic search temporarily unavailable" | Weaviate down or weights missing | `make docker-up`; check logs in backend; first call downloads weights |
| `make reindex` slow on first run | Downloading weights + CPU embedding | Expected; subsequent runs hit cache |

## All Makefile commands

```
Backend
  make venv                  Create virtual environment at backend/venv
  make install-backend       Install Python packages from requirements.txt
  make makemigrations msg=x  Generate Alembic migration file from models
  make migrate               Apply pending migrations to the database
  make run-backend           Run FastAPI dev server (port 8000)

Semantic Search
  make install-ml-cpu        Install PyTorch (CPU) and ML deps
  make install-ml-gpu        Install PyTorch (CUDA 12.4) and ML deps
  make check-ml-env          Smoke-test ML stack (loads BGE encoder)
  make reindex               Rebuild Weaviate collections from PostgreSQL products

Frontend
  make install-frontend      Install Node packages (npm install)
  make run-frontend          Run Vite dev server (port 5173)

Docker
  make docker-up             Start PostgreSQL + Weaviate + Redis
  make docker-down           Stop Docker services
  make docker-logs           View Docker service logs

Data
  make seed                  Reset schema + validate + re-run all seeds
```

Backend commands execute via `backend/venv/bin/` — never assume a globally
activated venv.
