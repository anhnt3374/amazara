---
feature: search
doc_type: architecture
tags: [milvus, embeddings, schema]
---

# Search — Architecture

## Two Milvus collections

### `product_image_vec_v1` — one row per image

| Field | Type | Notes |
|---|---|---|
| `id` (PK) | VARCHAR(64) | `<product_id>:<image_idx>` |
| `product_id` | VARCHAR(36) | indexed; used to group |
| `category_id` | VARCHAR(36) nullable | indexed; used in filter expr |
| `brand_id` | VARCHAR(36) nullable | indexed |
| `image_idx` | INT8 | order within product |
| `embedding` | FLOAT_VECTOR(768) | L2-normalized; metric IP |

### `product_desc_vec_v1` — one row per product

| Field | Type | Notes |
|---|---|---|
| `id` (PK) | VARCHAR(36) | = `product_id` |
| `category_id` | VARCHAR(36) nullable | indexed |
| `brand_id` | VARCHAR(36) nullable | indexed |
| `embedding` | FLOAT_VECTOR(384) | L2-normalized; metric IP |

Vector index: IVF_FLAT, nlist=128, nprobe=16 (defaults; configurable).

## Module boundaries

- `embedders/*` — model + tensor → vector. No DB, no Milvus.
- `vector_store.py` — Milvus only. No model.
- `cache.py` — pluggable backend behind a single `SearchCache` protocol.
- `search_service.py` — only orchestrator. The endpoint and CRUD layer
  import nothing else from `services/search`.

## MySQL ↔ Milvus

MySQL is source of truth for all metadata. Milvus stores vectors plus
the minimal scalar fields needed for filter and grouping. The service
returns `[(product_id, score)]`; the caller hydrates `Product` rows.

## Pluggable cache

`SearchCache` is a Protocol with two implementations:

- `InMemoryTTLCache` — `cachetools.TTLCache`, per-process.
- `RedisCache` — shared across uvicorn workers, survives restart.

If Redis is configured and unreachable, both `get` and `set` fail soft and
the request continues without cache; the endpoint never 5xx because of
cache.
