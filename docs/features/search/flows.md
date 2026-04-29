---
feature: search
doc_type: flows
tags: [pipeline, query, indexing]
---

# Search — Flows

## Indexing flow (offline)

`make reindex` → `python scripts/reindex_products.py`.

```
Load all Product rows → batch (default 64) →
  per batch:
    encode descriptions with BGE-small (one call)
    split image URLs by '|', keep first MAX_IMAGES_PER_PRODUCT
    fetch images concurrently (aiohttp)
    encode images with FG-CLIP 2
    L2-normalize all vectors
    upsert into both Milvus collections
flush + reload + clear cache
```

Failures in image download are logged and skipped; the product is still
indexed if its description embeds successfully.

## Query flow

```
[0] cache lookup by (query, brand_ids, category_ids) — hit returns
[1] resolve filters: brand_ids → category_ids, intersect with user-supplied
[2] encode query: FG-CLIP 2 text encoder + BGE-small (sync calls)
[3] ANN search image collection (top-500) and text collection (top-500),
    in parallel via run_in_executor
[4] aggregate image rows: per product_id, mean of top-3 scores
[5] fuse: min-max normalize each side, weighted sum (α=0.5)
[6] outlier cut: drop items below 0.6 × top1
[7] cache store full ranked list
[8] post-rank sort (if user sort != relevance), paginate, hydrate Product
    rows from MySQL, compute facets from candidate set
```

Latency budget on warm GPU: ~50–80 ms.
