---
feature: search
doc_type: architecture
tags: [weaviate, embeddings, schema]
---

# Search — Architecture

## Two Weaviate collections

### `ProductImageVecV1` — one object per image

| Property | Type | Notes |
|---|---|---|
| (UUID) | UUID5 | derived from `<product_id>:<image_idx>` for idempotent upsert |
| `product_id` | TEXT | indexed; used to group |
| `category_id` | TEXT | indexed; used in pre-filter allow-list |
| `brand_id` | TEXT | indexed |
| `image_idx` | INT | order within product |
| `image_key` | TEXT | original `<product_id>:<image_idx>` string |
| (vector) | FLOAT[768] | L2-normalized; cosine distance metric |

### `ProductDescVecV1` — one object per product

| Property | Type | Notes |
|---|---|---|
| (UUID) | UUID5 | derived from `product_id` |
| `product_id` | TEXT | indexed |
| `category_id` | TEXT | indexed |
| `brand_id` | TEXT | indexed |
| (vector) | FLOAT[384] | L2-normalized; cosine distance metric |

Vector index: HNSW (Weaviate default). Filter strategy: `ACORN` (default
since Weaviate v1.34) — pre-filtered ANN with inverted-index allow-list.

## Module boundaries

- `embedders/*` — model + tensor → vector. No DB, no vector store.
- `vector_store.py` — Weaviate only. No model.
- `cache.py` — pluggable backend behind a single `SearchCache` protocol.
- `search_service.py` — only orchestrator. The endpoint and CRUD layer
  import nothing else from `services/search`.

## PostgreSQL ↔ Weaviate

PostgreSQL is source of truth for all metadata. Weaviate stores vectors plus
the minimal scalar fields needed for filter and grouping. The service
returns `[(product_id, score)]`; the caller hydrates `Product` rows.

## Pluggable cache

`SearchCache` is a Protocol with two implementations:

- `InMemoryTTLCache` — `cachetools.TTLCache`, per-process.
- `RedisCache` — shared across uvicorn workers, survives restart.

If Redis is configured and unreachable, both `get` and `set` fail soft and
the request continues without cache; the endpoint never 5xx because of
cache.
