---
feature: search
doc_type: spec
tags: [semantic-search, milvus, fg-clip2, bge-small, embeddings, vector-search, design]
status: approved-for-planning
created: 2026-04-28
---

# Semantic Search — Design Spec

## 1. Goal

Replace the current `description ILIKE %term%` search at `GET /products/search`
with a semantic-search pipeline that ranks products using BOTH:

1. **Image embeddings** — multiple images per product, aggregated.
2. **Description embeddings** — one per product.

The text query is encoded twice (one encoder per modality) and the two
similarity signals are fused into a single ranking. After ranking, items far
below the top score are dropped, and the result is paginated.

## 2. Non-goals

- Image-upload as query input (text-only query for v1; reserved for future).
- Auto-incremental reindex on Product CRUD (manual CLI only for v1).
- Multilingual queries (English-only target; FG-CLIP 2 supports ZH but the
  product corpus is English).
- Replacing the lexical filter for the `search`-empty case — when no query is
  provided, the existing flow (filter + sort + paginate) is kept untouched.

## 3. Models

| Role | Model | Dim | License | Notes |
|---|---|---|---|---|
| Image encoder + Text encoder for image-side query | `qihoo360/fg-clip2-base` | 512 | Apache 2.0 | ViT-B/16 backbone; joint image/text space. |
| Text encoder for description-side query | `BAAI/bge-small-en-v1.5` | 384 | Apache 2.0 | 33M params, 512-token context, top-tier MTEB retrieval for its size. |

Rationale: FG-CLIP 2's text encoder must be used on the image-side query so
the query lands in the same joint space as image embeddings. BGE-small was
chosen over MiniLM-L6-v2 because Nike-style descriptions are 200–400 tokens
and MiniLM truncates at 256, and BGE-small is materially stronger on retrieval
benchmarks while remaining lightweight.

Both choices and the variant size are configurable (see §10).

## 4. Architecture

### 4.1 Module layout

```
backend/app/
├── core/config.py                       # extend Settings with SEMANTIC_* vars
└── services/search/                     # NEW
    ├── __init__.py
    ├── embedders/
    │   ├── base.py                      # ABCs: ImageEmbedder, TextEmbedder
    │   ├── fgclip.py                    # FG-CLIP 2 wrapper (image + text)
    │   └── bge.py                       # BGE-small wrapper
    ├── vector_store.py                  # Milvus client + collection schemas
    ├── image_fetcher.py                 # async URL → PIL.Image, retry, skip-on-error
    ├── aggregator.py                    # per-product image-score aggregation
    ├── fusion.py                        # min-max norm + weighted sum + outlier cut
    ├── cache.py                         # SearchCache protocol + in-memory + Redis impls
    ├── exceptions.py                    # SemanticSearchError hierarchy
    └── search_service.py                # orchestrator entry point

backend/scripts/
├── reindex_products.py                  # NEW: offline indexing CLI
└── check_ml_env.py                      # NEW: ML stack smoke test

backend/tests/search/                    # NEW
├── test_aggregator.py
├── test_fusion.py
├── test_image_fetcher.py
├── test_cache.py
└── test_search_service_int.py           # @pytest.mark.integration

docs/features/search/                    # NEW (created during implementation)
├── overview.md
├── architecture.md
└── flows.md
```

### 4.2 Module boundaries

- `embedders/*` — knows model + tensor → vector. Does not know the DB or Milvus.
- `vector_store.py` — knows Milvus collection schema and operations. Does not know any model.
- `cache.py` — pluggable. In-memory and Redis backends behind a single `SearchCache` protocol.
- `search_service.py` — the only orchestrator. Caller (`crud/product.py`) imports nothing else from `services/search`.
- `crud/product.py::search_products()` — applies scalar filters (brand/category) at MySQL/Milvus boundary, calls `search_service.semantic_search()`, hydrates Product rows from MySQL by ordered IDs.

### 4.3 Lazy-loaded singletons

Encoder models are loaded on first use (not at FastAPI startup) to keep the
backend bootable without GPU/weights and to keep tests fast. Singletons are
stored in module-level globals guarded by an `asyncio.Lock`.

## 5. Data model — Milvus

Two collections, distinct because dimensions and cardinalities differ.

### 5.1 `product_image_vec_v1` — one row per image

| Field | Type | Notes |
|---|---|---|
| `id` | VARCHAR(64), PK | `<product_id>:<image_idx>` |
| `product_id` | VARCHAR(36) | scalar field, indexed (used for grouping & filter) |
| `category_id` | VARCHAR(36) nullable | scalar, indexed (filter) |
| `brand_id` | VARCHAR(36) nullable | scalar, indexed (filter) |
| `image_idx` | INT8 | 0..N-1 within product |
| `embedding` | FLOAT_VECTOR(512) | L2-normalized; metric `IP` (cosine) |

Vector index: `IVF_FLAT`, `nlist=128`, `nprobe=16`.

### 5.2 `product_desc_vec_v1` — one row per product

| Field | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36), PK | = `product_id` |
| `category_id` | VARCHAR(36) nullable | scalar |
| `brand_id` | VARCHAR(36) nullable | scalar |
| `embedding` | FLOAT_VECTOR(384) | L2-normalized; metric `IP` |

Vector index: `IVF_FLAT`, `nlist=128`, `nprobe=16`.

### 5.3 Why denormalize `category_id` / `brand_id` into Milvus

Filters apply *before* ANN inside the Milvus query (`expr` argument) instead of
post-filtering after ANN. Without this, top-N could be dominated by items the
user has filtered out. Trade-off: when a product changes category, both
collections must be updated (handled by reindex; auto-CRUD sync is future
work).

### 5.4 Versioned collection names

Collections suffixed `_v1`. Schema/model changes ship as `_v2` built in
parallel and swapped atomically by config flip — no downtime migration.

### 5.5 MySQL ↔ Milvus boundary

MySQL is source of truth for all product metadata. Milvus stores only vectors
plus the minimal scalars needed for filter/group. `search_service` returns
`list[(product_id, score)]`; the caller hydrates `Product` rows from MySQL.

## 6. Indexing pipeline (offline CLI)

Entry: `backend/scripts/reindex_products.py`, exposed as `make reindex`.

### 6.1 Flow

```
[1] Load all Product rows from MySQL
    (id, name, description, image, category_id, brand_id)
[2] Chunk into batches of size SEMANTIC_INDEX_BATCH_PRODUCTS (default 64)
[3] For each batch:
    a. Encode descriptions with BGE-small (one encode call per batch)
    b. For each product: split image URLs by "|", keep first
       SEMANTIC_MAX_IMAGES_PER_PRODUCT
    c. Concurrent fetch images (aiohttp,
       SEMANTIC_IMAGE_FETCH_CONCURRENCY=16) → list[PIL.Image]
    d. Encode image batch with FG-CLIP 2 image encoder, batch size
       SEMANTIC_INDEX_BATCH_IMAGES
    e. L2-normalize all vectors
    f. Upsert into both collections (Milvus 2.4 upsert by PK)
    g. Drop tensors and image bytes — no disk persistence
[4] Flush collections, ensure they are loaded
[5] Clear search cache (SearchCache.clear())
```

### 6.2 CLI flags

```bash
python scripts/reindex_products.py \
  --batch-size-products 64 \
  --image-batch-size 32 \
  --max-images-per-product 4 \
  --product-ids id1,id2          # subset reindex
  --skip-images                  # debug
  --skip-descriptions            # debug
  --rebuild                      # drop & recreate collections
```

### 6.3 Idempotency

- Upsert by PK; rerunning does not produce duplicates.
- `--rebuild` provides a clean slate when schema changes.

### 6.4 Index-time error handling

| Situation | Behavior |
|---|---|
| Image URL timeout / 404 / corrupted bytes | Log warning, skip that image, continue with the product's other images. |
| Product has no valid images at all | Insert into `product_desc_vec` only. Query-time `image_score = 0` for it. |
| Empty / NULL description | Skip insert into `product_desc_vec`. Query-time `text_score = 0`. |
| OOM on image batch | Catch, retry with `batch_size // 2`. If batch_size=1 still OOMs, log error and skip product. |

### 6.5 Progress + resume

- Progress logged every 100 products.
- On crash, partial commits are durable in Milvus → rerun with `--product-ids`
  for the leftover set.
- Per-run audit log: `backend/logs/reindex_<timestamp>.log` lists every
  skipped product and reason.

## 7. Query pipeline

Entry: `GET /products/search` keeps its current signature. When `search` is
present, the request goes through the semantic path; otherwise it follows
the existing lexical-empty path (filter + sort + paginate).

### 7.1 Flow

```
[0] Cache lookup
    key = sha1("v1|" + query.strip().lower() + "|"
              + sorted(brand_ids) + "|" + sorted(category_ids))
    if hit  → ranked_full = cached, jump to step [8]
    if miss → run [1]–[7]

[1] Resolve filters
    brand_ids → category_ids (join via Category.brand_id) → intersect with
    user-supplied category_ids
    → milvus_filter_expr = "category_id in [...]"  (or None)

[2] Encode query (parallel)
    q_img = fgclip.encode_text(query)   # 512-dim, L2-norm
    q_txt = bge.encode_text(query)      # 384-dim, L2-norm

[3] ANN search (parallel)
    a = milvus.search(product_image_vec, q_img, top_k=ANN_TOPN_IMAGE,
                      expr=milvus_filter_expr)   # default 500
    b = milvus.search(product_desc_vec,  q_txt, top_k=ANN_TOPN_TEXT,
                      expr=milvus_filter_expr)   # default 500

[4] Aggregate image scores per product
    group `a` by product_id
    image_score(p) = mean of top-IMAGE_AGG_TOP_K scores in p's group
                     (default K=3; use whatever count is available if smaller)

[5] Fuse
    candidates = union(image_products, text_products) by product_id
    fill missing side with 0
    img_norm  = min-max-normalize(image_scores in candidates)
    text_norm = min-max-normalize(text_scores in candidates)
    final = α · img_norm + (1-α) · text_norm        # α = FUSION_ALPHA (0.5)

[6] Outlier filter
    sort candidates desc by final
    keep all items with final >= OUTLIER_RATIO_TAU · top1_final  (τ = 0.6)
    → ranked_full

[7] Cache store
    SearchCache.set(key, ranked_full, ttl=SEMANTIC_CACHE_TTL_SEC)

[8] Pagination + post-rank sort
    if user sort != "relevance":
        sort ranked_full by chosen field (price, created_at, discount, ...)
    page = clamp(page, 1, ceil(len(ranked_full) / PAGE_SIZE))
    page_ids = ranked_full[(page-1)*PAGE_SIZE : page*PAGE_SIZE]
    fetch Product rows from MySQL preserving order
    facets (available_brands, available_categories) computed from ranked_full
    → ProductSearchResponse
```

The cache key intentionally excludes `sort` and `page`: the full ranked list
is cached, so changing page or post-sort is an instant slice/sort.

### 7.2 Defaults (all configurable)

| Param | Default | Re-tunable without reindex? |
|---|---|---|
| `SEMANTIC_ANN_TOPN_IMAGE` | 500 | yes |
| `SEMANTIC_ANN_TOPN_TEXT` | 500 | yes |
| `SEMANTIC_IMAGE_AGG_TOP_K` | 3 | yes |
| `SEMANTIC_FUSION_ALPHA` | 0.5 | yes |
| `SEMANTIC_OUTLIER_RATIO_TAU` | 0.6 | yes |

### 7.3 Edge cases

| Case | Behavior |
|---|---|
| Both ANN lists empty (filter excludes everything) | return `{products: [], total: 0, ...}` |
| Image side empty (filtered set has no images) | image_score = 0 across the board → fusion degrades to text-only |
| Description side empty | symmetric — fusion degrades to image-only |
| `top1_final = 0` (degenerate) | skip outlier cut, return whole list |
| Query is one word | no special heuristic — same flow |

### 7.4 Latency budget (warm, GPU prod)

- Encode 2 queries (parallel): 10–20 ms
- 2 ANN searches (parallel, ~150–200K vectors): 20–40 ms
- Fuse + filter + MySQL hydrate: 10–20 ms
- **Total: ~50–80 ms**

Cold start (first request after boot, model load): 5–15 s. Subsequent
requests warm.

## 8. Cache

### 8.1 Pluggable backend

```python
class SearchCache(Protocol):
    async def get(self, key: str) -> list[tuple[str, float]] | None: ...
    async def set(self, key: str, value: list[tuple[str, float]], ttl: int) -> None: ...
    async def clear(self) -> None: ...
```

Two implementations:
- `InMemoryTTLCache` — `cachetools.TTLCache` backed.
- `RedisCache` — `redis.asyncio` backed, JSON-serialized values.

Selected via `SEMANTIC_CACHE_BACKEND ∈ {"memory", "redis"}`.

### 8.2 Trade-offs

|  | In-memory | Redis |
|---|---|---|
| Setup cost | Zero | Add container |
| Multi-worker uvicorn | Per-worker cache (low hit rate) | Shared (high hit rate) |
| Survives restart | No | Yes |
| Recommended for | Dev / single-worker | Production |

### 8.3 Infra change

Add `redis:7-alpine` service to `infra/docker-compose.yml` (port 6379).
Optional — required only when `SEMANTIC_CACHE_BACKEND=redis`.

### 8.4 Cache invalidation

- Primary: TTL (default 600s).
- On `make reindex`: script calls `SearchCache.clear()` at end.
- No invalidation on Product CRUD (irrelevant in v1; future work for stage C).

### 8.5 Failure mode

If Redis is configured but unreachable, `RedisCache` catches the connection
error, logs a warning, and behaves as a cache miss. The cache is a
performance optimization — its failure must not produce a 5xx.

## 9. Configuration surface

Extend `backend/app/core/config.py`. All new settings read from env, with safe
dev defaults.

```python
class Settings(BaseSettings):
    # === existing fields ===
    ...

    # === Semantic search: models ===
    SEMANTIC_FGCLIP_MODEL: str = "qihoo360/fg-clip2-base"
    SEMANTIC_TEXT_MODEL: str = "BAAI/bge-small-en-v1.5"
    SEMANTIC_DEVICE: str = "auto"          # auto | cuda | cpu
    SEMANTIC_FGCLIP_DIM: int = 512
    SEMANTIC_TEXT_DIM: int = 384
    SEMANTIC_HF_CACHE_DIR: str | None = None

    # === Semantic search: indexing ===
    SEMANTIC_INDEX_BATCH_PRODUCTS: int = 64
    SEMANTIC_INDEX_BATCH_IMAGES: int = 32
    SEMANTIC_MAX_IMAGES_PER_PRODUCT: int = 4
    SEMANTIC_IMAGE_FETCH_TIMEOUT_SEC: int = 10
    SEMANTIC_IMAGE_FETCH_RETRIES: int = 2
    SEMANTIC_IMAGE_FETCH_CONCURRENCY: int = 16

    # === Semantic search: Milvus ===
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    SEMANTIC_COLLECTION_IMAGE: str = "product_image_vec_v1"
    SEMANTIC_COLLECTION_TEXT: str = "product_desc_vec_v1"
    SEMANTIC_MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    SEMANTIC_MILVUS_NLIST: int = 128
    SEMANTIC_MILVUS_NPROBE: int = 16

    # === Semantic search: query ===
    SEMANTIC_ANN_TOPN_IMAGE: int = 500
    SEMANTIC_ANN_TOPN_TEXT: int = 500
    SEMANTIC_IMAGE_AGG_TOP_K: int = 3
    SEMANTIC_FUSION_ALPHA: float = 0.5
    SEMANTIC_OUTLIER_RATIO_TAU: float = 0.6

    # === Semantic search: cache ===
    SEMANTIC_CACHE_BACKEND: str = "memory"   # memory | redis
    SEMANTIC_CACHE_TTL_SEC: int = 600
    SEMANTIC_CACHE_MAX_ENTRIES: int = 1024
    REDIS_URL: str = "redis://localhost:6379/0"
```

Validators:
- `SEMANTIC_FUSION_ALPHA ∈ [0.0, 1.0]`
- `SEMANTIC_OUTLIER_RATIO_TAU ∈ [0.0, 1.0]`
- `SEMANTIC_DEVICE ∈ {"auto", "cuda", "cpu"}`
- `SEMANTIC_CACHE_BACKEND ∈ {"memory", "redis"}`

Invalid values fail fast at startup.

`.env.example` gets a corresponding semantic-search block (commented Redis
URL).

## 10. Dependencies & version pinning

Python target: **3.13**.

### 10.1 New deps

Split `backend/requirements.txt` into:

```
backend/requirements-base.txt           # FastAPI, SQLAlchemy, ... (existing pins)
backend/requirements-ml.txt             # ML / vector deps
backend/requirements.txt                # -r requirements-base.txt
                                        # -r requirements-ml.txt
```

`requirements-ml.txt`:

```
torch==2.6.0
torchvision==0.21.0
transformers==4.46.3
sentence-transformers==3.3.1
huggingface-hub==0.26.2
pillow==10.4.0
numpy==1.26.4
einops==0.8.0
pymilvus==2.4.9
marshmallow==3.21.3
cachetools==5.5.0
redis==5.2.0
```

### 10.2 Pinning rationale

| Pair | Reason |
|---|---|
| `torch==2.6.0` + `torchvision==0.21.0` | Lowest pair shipping Python 3.13 wheels on `download.pytorch.org/whl/cpu` and `whl/cu124`. torch 2.5.1 / torchvision 0.20.1 (an earlier draft pin) have no cp313 wheels. |
| `transformers==4.46.3` | Supports Python 3.13 and required for FG-CLIP 2 loader. Only requires `torch>=2.0`, so torch 2.6.0 is compatible. |
| `numpy==1.26.4` | Avoid numpy 2 ABI mix; safest under transformers 4.46. |
| `sentence-transformers==3.3.1` | Compatible with transformers 4.46 and torch 2.6. |
| `pymilvus==2.4.9` | Matches Milvus server `v2.4.1` already pinned in docker-compose. |
| `marshmallow==3.21.3` | pymilvus 2.4.9 transitively requires `environs`, which only works with marshmallow 3.x (uses `__version_info__`, removed in marshmallow 4). Without this pin, pip resolves to marshmallow 4 and pymilvus import fails. |
| `pillow==10.4.0` | Required by torchvision 0.21; avoids 11.x wheel issues on 3.13. |

### 10.3 GPU vs CPU wheel

When pulling from `download.pytorch.org/whl/...`, the local-version suffix
`+cpu` or `+cu124` is required because that index hosts wheels labeled with
that suffix.

- Production GPU (CUDA 12.4):
  `pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.6.0+cu124 torchvision==0.21.0+cu124`
- Dev CPU:
  `pip install --index-url https://download.pytorch.org/whl/cpu torch==2.6.0+cpu torchvision==0.21.0+cpu`

`requirements-ml.txt` does not pin an index URL; the install step (Dockerfile
or local `make`) picks the appropriate one. Documented in
`docs/features/search/setup.md`.

### 10.4 Smoke test

`backend/scripts/check_ml_env.py` imports torch, transformers,
sentence-transformers, pymilvus, encodes one dummy sentence, asserts shape.
Wired as `make check-ml-env`.

### 10.5 Risks & mitigation

- **`trust_remote_code` for FG-CLIP 2**: scoped to the `embedders/fgclip.py`
  loader only; documented; not enabled globally.
- **Wheel availability for 3.13**: all listed deps have 3.13 wheels as of
  April 2026. Build-from-source is the documented fallback.

## 11. Error handling

### 11.1 Exception hierarchy

```python
class SemanticSearchError(Exception): ...
class EmbedderUnavailable(SemanticSearchError): ...      # model load fail
class VectorStoreUnavailable(SemanticSearchError): ...   # Milvus down
class CacheUnavailable(SemanticSearchError): ...         # caught internally,
                                                         # not propagated
```

### 11.2 Layering

| Layer | When | Behavior |
|---|---|---|
| Indexing | URL fail / OOM / corrupted image | Log + skip — never crash the run. |
| Query — recoverable | Milvus connection lost / timeout | Raise `VectorStoreUnavailable` → endpoint maps to `503` "semantic search temporarily unavailable". No fallback to lexical (semantic is the new source of truth). |
| Query — bug | Embedder load fail / shape mismatch / NaN | Raise `EmbedderUnavailable` with full stacktrace logged → `503`. To fix, not to mask. |
| Cache | Redis unreachable | Log warning, treat as miss. Never 5xx because of cache. |

The product endpoint catches `SemanticSearchError` only — never bare
`Exception` — so unrelated bugs surface clearly.

### 11.3 Cases without explicit handling

These do not need error code paths because they are handled by routing or by
fusion:

- Empty query (routes to existing lexical-empty path).
- Product with no images (image_score = 0 in fusion).
- Pagination overflow (clamped, same as today).

## 12. Testing

### 12.1 Unit tests (no Milvus, no real models)

| File | Cases |
|---|---|
| `test_aggregator.py` | top-K mean with K=3 and ≥3 images; top-K mean with 1 image (degenerate); empty group → 0; input order independence. |
| `test_fusion.py` | min-max norm with all-equal scores (div-by-zero fallback); union with product on one side only; α=0 → text-only; α=1 → image-only; τ outlier (top1=0.9 → cut at 0.54); all scores 0 edge case. |
| `test_image_fetcher.py` | mocked HTTP returning 200/404/timeout; skip-on-error; concurrency limit respected. |
| `test_cache.py` | InMemoryTTLCache get/set/expire; key normalization (brand_ids order-independent); 1-char query change → different key. |

### 12.2 Integration tests (require Milvus)

Marked `@pytest.mark.integration` so light CI can skip.

| File | Cases |
|---|---|
| `test_search_service_int.py` | Index 5 fake products with mock vectors (`torch.randn`) → search → assert ranking matches hand-computed similarity; brand filter excludes other brands; cache hit on second call (mock encoder counter). |

### 12.3 ML stack smoke

`check_ml_env.py` runs as `@pytest.mark.ml`, opt-in or GPU CI.

### 12.4 Skipped on purpose

- API contract for `/products/search` — existing tests cover; signature unchanged.
- Thin embedder wrappers that just call `transformers` — covered by integration.
- Direct pymilvus calls — covered by integration.

### 12.5 Coverage targets

- `aggregator.py`, `fusion.py`, `cache.py`: 100% line coverage.
- Other modules: best-effort, no coverage gate.

## 13. Open issues / future work

- **Auto-incremental reindex** on Product CRUD (stage C): event hooks or
  background queue. Out of scope for v1.
- **Image-as-query** mode: same image collection can serve it; need new
  endpoint and request body.
- **Hybrid lexical + semantic**: future evaluation if recall on rare-token
  queries (e.g. exact SKU codes) regresses. Mitigation if needed: add lexical
  recall stream and RRF-merge.
- **Reranker model**: a small cross-encoder over the top-K could improve
  precision; deferred until measured need.
- **Multilingual**: FG-CLIP 2 supports ZH; description encoder would need swapping.

## 14. References

- [qihoo360/fg-clip2-base · Hugging Face](https://huggingface.co/qihoo360/fg-clip2-base)
- [qihoo360/fg-clip2-so400m · Hugging Face](https://huggingface.co/qihoo360/fg-clip2-so400m)
- [FG-CLIP 2 project page](https://360cvgroup.github.io/FG-CLIP/)
- [BAAI/bge-small-en-v1.5 · Hugging Face](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [Milvus 2.4 docs](https://milvus.io/docs/v2.4.x)
