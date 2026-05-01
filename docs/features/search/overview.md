---
feature: search
doc_type: overview
tags: [semantic-search, weaviate, fg-clip2, bge-small, embeddings]
---

# Search — Overview

`GET /products/search` ranks products by combining two semantic signals:

1. **Image similarity** — each product's images are embedded with FG-CLIP 2;
   the query text is encoded by FG-CLIP 2's text encoder and compared
   against image embeddings in the joint space.
2. **Description similarity** — each product description is embedded with
   BGE-small-en-v1.5; the query text is encoded by the same model and
   compared against description embeddings.

The two scores are normalized and fused (`α=0.5` by default). Items below
`0.6 × top1_final` are dropped. Results are paginated. The whole ranked
list is cached per `(query, brand_ids, category_ids)` for 10 minutes.

When `search` is empty, the endpoint falls back to filter-only listing
(no Weaviate call, no encoding).

## Where things live

| Concern | File |
|---|---|
| Orchestrator | `app/services/search/search_service.py` |
| Image encoder + text-side encoder for image | `app/services/search/embedders/fgclip.py` |
| Description encoder | `app/services/search/embedders/bge.py` |
| Weaviate client + schemas | `app/services/search/vector_store.py` |
| Image download | `app/services/search/image_fetcher.py` |
| Score aggregation (top-K mean) | `app/services/search/aggregator.py` |
| Score fusion + outlier cut | `app/services/search/fusion.py` |
| Result cache (memory or Redis) | `app/services/search/cache.py` |
| Indexing CLI | `scripts/reindex_products.py` |

## Tunable settings

All parameters live on `Settings` (env-driven). The most useful ones:

| Env | Default | Effect |
|---|---|---|
| `SEMANTIC_FUSION_ALPHA` | `0.8` | image weight; text = 1−α |
| `SEMANTIC_OUTLIER_RATIO_TAU` | `0.6` | drop items below τ × top1 |
| `SEMANTIC_IMAGE_AGG_TOP_K` | `3` | mean of K best images per product |
| `SEMANTIC_ANN_TOPN_IMAGE` | `500` | ANN limit, image side |
| `SEMANTIC_ANN_TOPN_TEXT` | `500` | ANN limit, text side |
| `SEMANTIC_CACHE_BACKEND` | `memory` | `memory` or `redis` |

Changing these does not require reindexing. Changing models or collection
names does (build a `_v2` collection and flip).
