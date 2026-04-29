# Semantic Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `description ILIKE` lexical search at `GET /products/search` with a semantic-search pipeline that fuses image-embedding similarity (FG-CLIP 2) and description-embedding similarity (BGE-small).

**Architecture:** Two Milvus collections (`product_image_vec_v1` for per-image vectors, `product_desc_vec_v1` for per-product vectors). Indexing is an offline CLI; query path encodes the search string with both encoders, runs two ANN searches in parallel, aggregates per-product image scores via top-K mean, fuses into a single ranking with min-max normalization + weighted sum, drops items below `0.6 × top1`, paginates. Results cached per `(query, brand_ids, category_ids)` via a pluggable in-memory or Redis cache.

**Tech Stack:** FastAPI · SQLAlchemy 2 · MySQL · Milvus 2.4 · PyTorch 2.5 · transformers 4.46 · sentence-transformers 3.3 · Pillow · aiohttp · cachetools · redis-py · Python 3.13

**Spec:** `docs/superpowers/specs/2026-04-28-semantic-search-design.md`

---

## File Structure

### Created

```
backend/requirements-base.txt                         # existing pins, split out
backend/requirements-ml.txt                           # ML deps
backend/app/services/search/__init__.py
backend/app/services/search/exceptions.py             # SemanticSearchError hierarchy
backend/app/services/search/embedders/__init__.py
backend/app/services/search/embedders/base.py         # TextEmbedder, ImageEmbedder ABCs
backend/app/services/search/embedders/bge.py          # BGE-small wrapper
backend/app/services/search/embedders/fgclip.py       # FG-CLIP 2 wrapper
backend/app/services/search/aggregator.py             # per-product image-score aggregation
backend/app/services/search/fusion.py                 # min-max norm + weighted sum + outlier cut
backend/app/services/search/image_fetcher.py          # async URL → PIL.Image
backend/app/services/search/cache.py                  # SearchCache + impls
backend/app/services/search/vector_store.py           # Milvus client + schemas
backend/app/services/search/search_service.py         # orchestrator
backend/scripts/reindex_products.py                   # offline indexing CLI
backend/scripts/check_ml_env.py                       # ML smoke test
backend/tests/search/__init__.py
backend/tests/search/test_aggregator.py
backend/tests/search/test_fusion.py
backend/tests/search/test_image_fetcher.py
backend/tests/search/test_cache.py
backend/tests/search/test_search_service.py
docs/features/search/overview.md
docs/features/search/architecture.md
docs/features/search/flows.md
```

### Modified

```
backend/requirements.txt                              # delegates to base + ml
backend/app/core/config.py                            # add SEMANTIC_* fields + validators
backend/app/crud/product.py                           # search_products() routes via search_service
backend/app/api/v1/endpoints/product.py               # no signature change; pass-through
infra/docker-compose.yml                              # add redis service
.env.example                                          # add semantic-search block
Makefile                                              # add reindex / check-ml-env / install-ml-cpu / install-ml-gpu
docs/index/feature-map.md                             # register search feature
```

---

## Task 1: Split requirements and add ML deps

**Files:**
- Create: `backend/requirements-base.txt`, `backend/requirements-ml.txt`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Move existing pins into `requirements-base.txt`**

Create `backend/requirements-base.txt` with the exact contents of the current `backend/requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pymysql==1.1.1
alembic==1.13.3
python-jose[cryptography]==3.3.0
bcrypt==4.2.0
python-dotenv==1.0.1
pydantic-settings==2.5.2
pydantic[email]==2.9.2
python-multipart==0.0.12
aiohttp==3.10.10
langgraph>=0.2,<1
langsmith>=0.3,<1
```

- [ ] **Step 2: Create `backend/requirements-ml.txt`**

```
torch==2.11.0
torchvision==0.26.0
transformers>=4.56,<5
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

> **marshmallow note:** pymilvus 2.4.9 transitively depends on `environs`, which
> only works with marshmallow 3.x (uses `__version_info__`, removed in
> marshmallow 4). Without this pin, pip resolves to 4.x and pymilvus import
> fails at runtime.

- [ ] **Step 3: Replace `backend/requirements.txt` to delegate**

```
-r requirements-base.txt
-r requirements-ml.txt
```

- [ ] **Step 4: Reinstall in the venv (CPU wheel for dev)**

Run:
```bash
backend/venv/bin/pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements-base.txt
backend/venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0+cpu torchvision==0.26.0+cpu
backend/venv/bin/pip install -r backend/requirements-ml.txt
```

> **Pin note:** torch 2.6.0 + torchvision 0.21.0 is the lowest pair that ships
> Python 3.13 CPU wheels on `download.pytorch.org/whl/cpu`. The earlier draft
> of this plan used 2.5.1 / 0.20.1, but those have no cp313 wheels. The `+cpu`
> local-version suffix is required when pulling from this index. After this
> step, pip will see torch/torchvision already installed at the right versions
> when processing `requirements-ml.txt` and skip them.

Expected: all packages install without resolver errors. Confirm by running:
```bash
backend/venv/bin/python -c "import torch, transformers, sentence_transformers, pymilvus, redis, cachetools; print('OK')"
```
Expected output: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/requirements-base.txt backend/requirements-ml.txt
git commit -m "chore(deps): split requirements into base+ml, pin torch/transformers for py3.13"
```

---

## Task 2: Extend Settings with SEMANTIC_* fields

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Append new fields to `Settings`**

Open `backend/app/core/config.py`. Add the imports at the top:

```python
from typing import Literal

from pydantic import Field, field_validator
```

Append the following fields inside the `Settings` class, before the `DATABASE_URL` property:

```python
    # ── Semantic search: models ────────────────────────────────────────────
    SEMANTIC_FGCLIP_MODEL: str = "qihoo360/fg-clip2-base"
    SEMANTIC_TEXT_MODEL: str = "BAAI/bge-small-en-v1.5"
    SEMANTIC_DEVICE: Literal["auto", "cuda", "cpu"] = "auto"
    SEMANTIC_FGCLIP_DIM: int = 768
    SEMANTIC_TEXT_DIM: int = 384
    SEMANTIC_HF_CACHE_DIR: str | None = None

    # ── Semantic search: indexing ──────────────────────────────────────────
    SEMANTIC_INDEX_BATCH_PRODUCTS: int = 64
    SEMANTIC_INDEX_BATCH_IMAGES: int = 32
    SEMANTIC_MAX_IMAGES_PER_PRODUCT: int = 4
    SEMANTIC_IMAGE_FETCH_TIMEOUT_SEC: int = 10
    SEMANTIC_IMAGE_FETCH_RETRIES: int = 2
    SEMANTIC_IMAGE_FETCH_CONCURRENCY: int = 16

    # ── Semantic search: Milvus ────────────────────────────────────────────
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    SEMANTIC_COLLECTION_IMAGE: str = "product_image_vec_v1"
    SEMANTIC_COLLECTION_TEXT: str = "product_desc_vec_v1"
    SEMANTIC_MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    SEMANTIC_MILVUS_NLIST: int = 128
    SEMANTIC_MILVUS_NPROBE: int = 16

    # ── Semantic search: query ─────────────────────────────────────────────
    SEMANTIC_ANN_TOPN_IMAGE: int = 500
    SEMANTIC_ANN_TOPN_TEXT: int = 500
    SEMANTIC_IMAGE_AGG_TOP_K: int = 3
    SEMANTIC_FUSION_ALPHA: float = 0.5
    SEMANTIC_OUTLIER_RATIO_TAU: float = 0.6

    # ── Semantic search: cache ─────────────────────────────────────────────
    SEMANTIC_CACHE_BACKEND: Literal["memory", "redis"] = "memory"
    SEMANTIC_CACHE_TTL_SEC: int = 600
    SEMANTIC_CACHE_MAX_ENTRIES: int = 1024
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("SEMANTIC_FUSION_ALPHA", "SEMANTIC_OUTLIER_RATIO_TAU")
    @classmethod
    def _check_unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("must be in [0.0, 1.0]")
        return v
```

- [ ] **Step 2: Verify `Settings()` still loads**

Run:
```bash
backend/venv/bin/python -c "from app.core.config import settings; print(settings.SEMANTIC_FGCLIP_MODEL)"
```
(run from `backend/` directory)

Expected output: `qihoo360/fg-clip2-base`

- [ ] **Step 3: Append a section to `.env.example`**

Append to `.env.example`:

```
# ── Semantic search ──────────────────────────────
SEMANTIC_FGCLIP_MODEL=qihoo360/fg-clip2-base
SEMANTIC_TEXT_MODEL=BAAI/bge-small-en-v1.5
SEMANTIC_DEVICE=auto

SEMANTIC_FUSION_ALPHA=0.5
SEMANTIC_OUTLIER_RATIO_TAU=0.6
SEMANTIC_IMAGE_AGG_TOP_K=3

SEMANTIC_ANN_TOPN_IMAGE=500
SEMANTIC_ANN_TOPN_TEXT=500

MILVUS_HOST=localhost
MILVUS_PORT=19530

SEMANTIC_CACHE_BACKEND=memory
SEMANTIC_CACHE_TTL_SEC=600
# REDIS_URL=redis://localhost:6379/0
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/config.py .env.example
git commit -m "feat(config): add SEMANTIC_* settings with validators"
```

---

## Task 3: Create exception hierarchy

**Files:**
- Create: `backend/app/services/search/__init__.py`
- Create: `backend/app/services/search/exceptions.py`

- [ ] **Step 1: Create empty package init**

Create `backend/app/services/search/__init__.py`:
```python
```
(empty file)

- [ ] **Step 2: Create exceptions module**

Create `backend/app/services/search/exceptions.py`:

```python
class SemanticSearchError(Exception):
    """Base class for all semantic-search runtime errors."""


class EmbedderUnavailable(SemanticSearchError):
    """Raised when an embedder fails to load or run."""


class VectorStoreUnavailable(SemanticSearchError):
    """Raised when Milvus is unreachable or returns an unrecoverable error."""


class CacheUnavailable(SemanticSearchError):
    """Raised internally when a cache backend is unreachable.

    Caught by the search service and treated as a cache miss; never
    propagated to API callers.
    """
```

- [ ] **Step 3: Smoke import**

Run from `backend/`:
```bash
backend/venv/bin/python -c "from app.services.search.exceptions import SemanticSearchError, EmbedderUnavailable, VectorStoreUnavailable, CacheUnavailable; print('OK')"
```
Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/search/__init__.py backend/app/services/search/exceptions.py
git commit -m "feat(search): add exception hierarchy"
```

---

## Task 4: Define embedder ABCs

**Files:**
- Create: `backend/app/services/search/embedders/__init__.py`
- Create: `backend/app/services/search/embedders/base.py`

- [ ] **Step 1: Create empty package init**

`backend/app/services/search/embedders/__init__.py`:
```python
```

- [ ] **Step 2: Create ABCs**

`backend/app/services/search/embedders/base.py`:

```python
from abc import ABC, abstractmethod

import numpy as np
from PIL.Image import Image


class TextEmbedder(ABC):
    """Encodes text strings into L2-normalized float32 vectors."""

    @property
    @abstractmethod
    def dim(self) -> int: ...

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return shape (len(texts), dim), L2-normalized, float32."""


class ImageEmbedder(ABC):
    """Encodes PIL images into L2-normalized float32 vectors."""

    @property
    @abstractmethod
    def dim(self) -> int: ...

    @abstractmethod
    def encode(self, images: list[Image]) -> np.ndarray:
        """Return shape (len(images), dim), L2-normalized, float32."""
```

- [ ] **Step 3: Smoke import**

```bash
backend/venv/bin/python -c "from app.services.search.embedders.base import TextEmbedder, ImageEmbedder; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/search/embedders/
git commit -m "feat(search): add embedder ABCs"
```

---

## Task 5: Implement aggregator with TDD

**Files:**
- Create: `backend/tests/search/__init__.py`, `backend/tests/search/test_aggregator.py`
- Create: `backend/app/services/search/aggregator.py`

- [ ] **Step 1: Create empty test package init**

`backend/tests/search/__init__.py`:
```python
```

- [ ] **Step 2: Write failing tests**

`backend/tests/search/test_aggregator.py`:

```python
import unittest

from app.services.search.aggregator import aggregate_image_scores


class AggregateImageScoresTest(unittest.TestCase):
    def test_top_k_mean_with_more_than_k_images(self) -> None:
        # product P has 5 image scores; top-3 mean = mean(0.9, 0.8, 0.7) = 0.8
        rows = [
            ("img1", "P", 0.5),
            ("img2", "P", 0.9),
            ("img3", "P", 0.7),
            ("img4", "P", 0.3),
            ("img5", "P", 0.8),
        ]
        result = aggregate_image_scores(rows, top_k=3)
        self.assertAlmostEqual(result["P"], 0.8, places=6)

    def test_top_k_mean_with_fewer_than_k_images(self) -> None:
        # only 2 images for P → mean of those 2
        rows = [("img1", "P", 0.6), ("img2", "P", 0.4)]
        result = aggregate_image_scores(rows, top_k=3)
        self.assertAlmostEqual(result["P"], 0.5, places=6)

    def test_multiple_products_independent(self) -> None:
        rows = [
            ("a", "P1", 0.9),
            ("b", "P1", 0.1),
            ("c", "P2", 0.4),
            ("d", "P2", 0.6),
        ]
        result = aggregate_image_scores(rows, top_k=1)
        self.assertAlmostEqual(result["P1"], 0.9, places=6)
        self.assertAlmostEqual(result["P2"], 0.6, places=6)

    def test_empty_rows_returns_empty_dict(self) -> None:
        self.assertEqual(aggregate_image_scores([], top_k=3), {})

    def test_input_order_does_not_matter(self) -> None:
        rows_a = [("x", "P", 0.1), ("y", "P", 0.9), ("z", "P", 0.5)]
        rows_b = [("y", "P", 0.9), ("z", "P", 0.5), ("x", "P", 0.1)]
        self.assertEqual(
            aggregate_image_scores(rows_a, top_k=2),
            aggregate_image_scores(rows_b, top_k=2),
        )

    def test_top_k_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_image_scores([("a", "P", 0.5)], top_k=0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to confirm failure**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_aggregator -v
```
Expected: ImportError because `aggregator` does not exist yet.

- [ ] **Step 4: Implement aggregator**

`backend/app/services/search/aggregator.py`:

```python
from collections import defaultdict
from collections.abc import Iterable


def aggregate_image_scores(
    rows: Iterable[tuple[str, str, float]],
    top_k: int,
) -> dict[str, float]:
    """Group per-image scores by product_id and reduce via top-K mean.

    Args:
        rows: iterable of (image_id, product_id, score). image_id is unused
            but kept in the row shape because that is what Milvus search
            results provide.
        top_k: number of highest-scoring images to average per product. If a
            product has fewer than top_k images in `rows`, the mean is taken
            over what is available.

    Returns:
        dict mapping product_id to the aggregated score.

    Raises:
        ValueError: if top_k <= 0.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    groups: dict[str, list[float]] = defaultdict(list)
    for _image_id, product_id, score in rows:
        groups[product_id].append(score)

    aggregated: dict[str, float] = {}
    for product_id, scores in groups.items():
        scores.sort(reverse=True)
        kept = scores[:top_k]
        aggregated[product_id] = sum(kept) / len(kept)
    return aggregated
```

- [ ] **Step 5: Run tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_aggregator -v
```
Expected: 6 tests, all pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/search/aggregator.py backend/tests/search/__init__.py backend/tests/search/test_aggregator.py
git commit -m "feat(search): per-product top-K mean image-score aggregator"
```

---

## Task 6: Implement fusion with TDD

**Files:**
- Create: `backend/tests/search/test_fusion.py`
- Create: `backend/app/services/search/fusion.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/search/test_fusion.py`:

```python
import unittest

from app.services.search.fusion import fuse_and_filter


class FuseAndFilterTest(unittest.TestCase):
    def test_alpha_zero_returns_text_only_ranking(self) -> None:
        image_scores = {"P1": 1.0, "P2": 0.0}      # would dominate at α>0
        text_scores = {"P1": 0.1, "P2": 0.9}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.0, tau=0.0)
        self.assertEqual([pid for pid, _ in ranked], ["P2", "P1"])

    def test_alpha_one_returns_image_only_ranking(self) -> None:
        image_scores = {"P1": 0.9, "P2": 0.1}
        text_scores = {"P1": 0.1, "P2": 0.9}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=1.0, tau=0.0)
        self.assertEqual([pid for pid, _ in ranked], ["P1", "P2"])

    def test_union_with_missing_side_filled_with_zero(self) -> None:
        image_scores = {"P1": 0.8}
        text_scores = {"P2": 0.8}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.0)
        ids = [pid for pid, _ in ranked]
        self.assertEqual(set(ids), {"P1", "P2"})

    def test_outlier_cut_at_tau_times_top1(self) -> None:
        # post-fusion finals should be 1.0, 0.7, 0.5, 0.0 (top-1 = 1.0)
        # tau=0.6 → cut at 0.6 → keep 1.0 and 0.7
        image_scores = {"A": 1.0, "B": 0.7, "C": 0.5, "D": 0.0}
        text_scores = {"A": 1.0, "B": 0.7, "C": 0.5, "D": 0.0}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.6)
        ids = [pid for pid, _ in ranked]
        self.assertEqual(ids, ["A", "B"])

    def test_all_equal_scores_does_not_div_by_zero(self) -> None:
        image_scores = {"A": 0.5, "B": 0.5, "C": 0.5}
        text_scores = {"A": 0.5, "B": 0.5, "C": 0.5}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.0)
        # all equal → all kept, finite numbers
        self.assertEqual(len(ranked), 3)
        for _pid, score in ranked:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_empty_inputs_returns_empty(self) -> None:
        self.assertEqual(fuse_and_filter({}, {}, alpha=0.5, tau=0.6), [])

    def test_top1_zero_skips_outlier_cut(self) -> None:
        # Pathological: all candidates have final score 0.
        image_scores = {"A": 0.0, "B": 0.0}
        text_scores = {"A": 0.0, "B": 0.0}
        ranked = fuse_and_filter(image_scores, text_scores, alpha=0.5, tau=0.6)
        self.assertEqual(len(ranked), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, confirm failure**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_fusion -v
```
Expected: ImportError.

- [ ] **Step 3: Implement fusion**

`backend/app/services/search/fusion.py`:

```python
def _min_max_normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    span = hi - lo
    if span == 0:
        return {k: 0.0 for k in values}
    return {k: (v - lo) / span for k, v in values.items()}


def fuse_and_filter(
    image_scores: dict[str, float],
    text_scores: dict[str, float],
    alpha: float,
    tau: float,
) -> list[tuple[str, float]]:
    """Combine image and text scores into a ranked list, then drop outliers.

    Args:
        image_scores: product_id → image-side score (already aggregated).
        text_scores: product_id → text-side score.
        alpha: weight of image side; text weight = 1 - alpha. In [0, 1].
        tau: keep candidates with final score >= tau * top1_final. In [0, 1].
            tau=0 disables the outlier cut.

    Returns:
        list of (product_id, final_score) sorted by final_score descending.
        Empty list if both inputs are empty.
    """
    candidate_ids = set(image_scores) | set(text_scores)
    if not candidate_ids:
        return []

    img_dict = {pid: image_scores.get(pid, 0.0) for pid in candidate_ids}
    txt_dict = {pid: text_scores.get(pid, 0.0) for pid in candidate_ids}

    img_norm = _min_max_normalize(img_dict)
    txt_norm = _min_max_normalize(txt_dict)

    finals = [
        (pid, alpha * img_norm[pid] + (1.0 - alpha) * txt_norm[pid])
        for pid in candidate_ids
    ]
    finals.sort(key=lambda x: x[1], reverse=True)

    top1 = finals[0][1]
    if top1 <= 0.0 or tau <= 0.0:
        return finals

    cutoff = tau * top1
    return [(pid, score) for pid, score in finals if score >= cutoff]
```

- [ ] **Step 4: Run tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_fusion -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/search/fusion.py backend/tests/search/test_fusion.py
git commit -m "feat(search): min-max norm + weighted-sum fusion + ratio outlier cut"
```

---

## Task 7: Implement async image fetcher with TDD

**Files:**
- Create: `backend/tests/search/test_image_fetcher.py`
- Create: `backend/app/services/search/image_fetcher.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/search/test_image_fetcher.py`:

```python
import asyncio
import io
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image

from app.services.search.image_fetcher import fetch_images


def _png_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    img = Image.new("RGB", (8, 8), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class FakeResp:
    def __init__(self, status: int, body: bytes = b"") -> None:
        self.status = status
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def read(self) -> bytes:
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")
        return self._body


class FakeSession:
    def __init__(self, mapping: dict[str, FakeResp]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        return self._mapping[url]

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class FetchImagesTest(unittest.TestCase):
    def test_fetches_all_ok_urls(self) -> None:
        urls = ["http://x/1.png", "http://x/2.png"]
        session = FakeSession({u: FakeResp(200, _png_bytes()) for u in urls})

        with patch(
            "app.services.search.image_fetcher.aiohttp.ClientSession",
            return_value=session,
        ):
            result = asyncio.run(
                fetch_images(urls, timeout_sec=1, retries=0, concurrency=4)
            )

        # all 2 fetched, all PIL.Image
        self.assertEqual(len(result), 2)
        for img in result:
            self.assertIsInstance(img, Image.Image)

    def test_skip_on_404(self) -> None:
        urls = ["http://x/ok.png", "http://x/missing.png"]
        session = FakeSession({
            "http://x/ok.png": FakeResp(200, _png_bytes()),
            "http://x/missing.png": FakeResp(404),
        })
        with patch(
            "app.services.search.image_fetcher.aiohttp.ClientSession",
            return_value=session,
        ):
            result = asyncio.run(
                fetch_images(urls, timeout_sec=1, retries=0, concurrency=4)
            )
        # only the 200 should yield an image; failed URL replaced with None
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Image.Image)
        self.assertIsNone(result[1])

    def test_skip_on_corrupted_bytes(self) -> None:
        urls = ["http://x/bad.png"]
        session = FakeSession({"http://x/bad.png": FakeResp(200, b"not an image")})
        with patch(
            "app.services.search.image_fetcher.aiohttp.ClientSession",
            return_value=session,
        ):
            result = asyncio.run(
                fetch_images(urls, timeout_sec=1, retries=0, concurrency=4)
            )
        self.assertEqual(result, [None])

    def test_empty_url_list(self) -> None:
        result = asyncio.run(
            fetch_images([], timeout_sec=1, retries=0, concurrency=4)
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, confirm failure**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_image_fetcher -v
```
Expected: ImportError.

- [ ] **Step 3: Implement fetcher**

`backend/app/services/search/image_fetcher.py`:

```python
from __future__ import annotations

import asyncio
import io
import logging

import aiohttp
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


async def _fetch_one(
    session: aiohttp.ClientSession,
    url: str,
    timeout_sec: int,
    retries: int,
) -> Image.Image | None:
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"HTTP {resp.status}")
                data = await resp.read()
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
                return img.convert("RGB")
            except (UnidentifiedImageError, OSError) as e:
                logger.warning("image decode failed for %s: %s", url, e)
                return None
        except Exception as e:  # noqa: BLE001 — retry on any network error
            last_error = e
            if attempt < retries:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
    logger.warning("image fetch failed for %s: %s", url, last_error)
    return None


async def fetch_images(
    urls: list[str],
    timeout_sec: int,
    retries: int,
    concurrency: int,
) -> list[Image.Image | None]:
    """Concurrently fetch and decode images.

    Returns a list aligned with `urls`. Failed entries are `None`; the caller
    is expected to skip them. Order is preserved.
    """
    if not urls:
        return []
    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:
        async def _bound(url: str) -> Image.Image | None:
            async with sem:
                return await _fetch_one(session, url, timeout_sec, retries)

        return await asyncio.gather(*(_bound(u) for u in urls))
```

- [ ] **Step 4: Run tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_image_fetcher -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/search/image_fetcher.py backend/tests/search/test_image_fetcher.py
git commit -m "feat(search): async image fetcher with retry and skip-on-error"
```

---

## Task 8: Cache protocol + InMemoryTTLCache

**Files:**
- Create: `backend/tests/search/test_cache.py`
- Create: `backend/app/services/search/cache.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/search/test_cache.py`:

```python
import asyncio
import time
import unittest

from app.services.search.cache import (
    InMemoryTTLCache,
    SearchCache,
    make_cache_key,
)


class MakeCacheKeyTest(unittest.TestCase):
    def test_key_normalizes_brand_order(self) -> None:
        a = make_cache_key("hello", ["b1", "b2"], ["c1"])
        b = make_cache_key("hello", ["b2", "b1"], ["c1"])
        self.assertEqual(a, b)

    def test_key_normalizes_query_case_and_whitespace(self) -> None:
        a = make_cache_key("Hello World", [], [])
        b = make_cache_key("  hello world  ", [], [])
        self.assertEqual(a, b)

    def test_key_changes_on_query_change(self) -> None:
        a = make_cache_key("hello", [], [])
        b = make_cache_key("hellp", [], [])
        self.assertNotEqual(a, b)


class InMemoryTTLCacheTest(unittest.TestCase):
    def test_get_set_roundtrip(self) -> None:
        cache: SearchCache = InMemoryTTLCache(max_entries=8, default_ttl_sec=60)
        value = [("p1", 0.9), ("p2", 0.8)]
        asyncio.run(cache.set("k", value, ttl=60))
        got = asyncio.run(cache.get("k"))
        self.assertEqual(got, value)

    def test_miss_returns_none(self) -> None:
        cache: SearchCache = InMemoryTTLCache(max_entries=8, default_ttl_sec=60)
        self.assertIsNone(asyncio.run(cache.get("missing")))

    def test_expiry(self) -> None:
        cache: SearchCache = InMemoryTTLCache(max_entries=8, default_ttl_sec=60)
        asyncio.run(cache.set("k", [("p", 1.0)], ttl=1))
        time.sleep(1.1)
        self.assertIsNone(asyncio.run(cache.get("k")))

    def test_clear(self) -> None:
        cache: SearchCache = InMemoryTTLCache(max_entries=8, default_ttl_sec=60)
        asyncio.run(cache.set("k", [("p", 1.0)], ttl=60))
        asyncio.run(cache.clear())
        self.assertIsNone(asyncio.run(cache.get("k")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, confirm failure**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_cache -v
```
Expected: ImportError.

- [ ] **Step 3: Implement cache module**

`backend/app/services/search/cache.py`:

```python
from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from typing import Protocol

from cachetools import TTLCache

logger = logging.getLogger(__name__)

RankedList = list[tuple[str, float]]


def make_cache_key(
    query: str,
    brand_ids: Iterable[str] | None,
    category_ids: Iterable[str] | None,
) -> str:
    norm_query = " ".join(query.lower().split())
    norm_brands = ",".join(sorted(brand_ids or []))
    norm_cats = ",".join(sorted(category_ids or []))
    payload = f"v1|{norm_query}|{norm_brands}|{norm_cats}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


class SearchCache(Protocol):
    async def get(self, key: str) -> RankedList | None: ...
    async def set(self, key: str, value: RankedList, ttl: int) -> None: ...
    async def clear(self) -> None: ...


class InMemoryTTLCache:
    def __init__(self, max_entries: int, default_ttl_sec: int) -> None:
        self._cache: TTLCache = TTLCache(maxsize=max_entries, ttl=default_ttl_sec)
        self._default_ttl = default_ttl_sec

    async def get(self, key: str) -> RankedList | None:
        return self._cache.get(key)

    async def set(self, key: str, value: RankedList, ttl: int) -> None:
        # cachetools TTLCache uses a single TTL; per-entry override is not
        # supported. Honor `ttl` only when it matches the cache TTL; otherwise
        # use the cache TTL silently. This is acceptable because the caller
        # always passes settings.SEMANTIC_CACHE_TTL_SEC.
        del ttl
        self._cache[key] = value

    async def clear(self) -> None:
        self._cache.clear()
```

- [ ] **Step 4: Run tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_cache -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/search/cache.py backend/tests/search/test_cache.py
git commit -m "feat(search): cache protocol + in-memory TTL implementation"
```

---

## Task 9: Add Redis cache backend + docker-compose service

**Files:**
- Modify: `backend/app/services/search/cache.py`
- Modify: `infra/docker-compose.yml`
- Modify: `backend/tests/search/test_cache.py`

- [ ] **Step 1: Add Redis service to docker-compose**

In `infra/docker-compose.yml`, append a new service before the `volumes:` block:

```yaml
  # ─────────────────────────────────────────
  # Redis (semantic search cache)
  # ─────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: shope_redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
```

Add `redis_data:` is **not** required (cache only). No new named volume.

- [ ] **Step 2: Append `RedisCache` to `cache.py`**

Append to `backend/app/services/search/cache.py`:

```python
import json

import redis.asyncio as aioredis

from app.services.search.exceptions import CacheUnavailable


class RedisCache:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client: aioredis.Redis | None = None

    async def _conn(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> RankedList | None:
        try:
            client = await self._conn()
            raw = await client.get(key)
        except Exception as e:  # noqa: BLE001
            logger.warning("redis get failed: %s", e)
            return None
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return [(pid, float(score)) for pid, score in data]
        except (ValueError, TypeError) as e:
            logger.warning("redis value decode failed: %s", e)
            return None

    async def set(self, key: str, value: RankedList, ttl: int) -> None:
        try:
            client = await self._conn()
            await client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:  # noqa: BLE001
            logger.warning("redis set failed: %s", e)

    async def clear(self) -> None:
        try:
            client = await self._conn()
            await client.flushdb()
        except Exception as e:  # noqa: BLE001
            raise CacheUnavailable(f"redis clear failed: {e}") from e


def build_cache_from_settings() -> SearchCache:
    """Factory used by search_service. Reads settings at call time."""
    from app.core.config import settings

    if settings.SEMANTIC_CACHE_BACKEND == "redis":
        return RedisCache(settings.REDIS_URL)
    return InMemoryTTLCache(
        max_entries=settings.SEMANTIC_CACHE_MAX_ENTRIES,
        default_ttl_sec=settings.SEMANTIC_CACHE_TTL_SEC,
    )
```

- [ ] **Step 3: Add Redis-failure test (mocked)**

Append to `backend/tests/search/test_cache.py`:

```python
class RedisCacheFailureTest(unittest.TestCase):
    def test_get_returns_none_on_connection_error(self) -> None:
        from unittest.mock import AsyncMock, patch

        from app.services.search.cache import RedisCache

        cache = RedisCache("redis://localhost:1/0")
        fake_client = AsyncMock()
        fake_client.get.side_effect = ConnectionError("nope")
        with patch.object(cache, "_conn", AsyncMock(return_value=fake_client)):
            result = asyncio.run(cache.get("k"))
        self.assertIsNone(result)
```

- [ ] **Step 4: Run all cache tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_cache -v
```
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/search/cache.py backend/tests/search/test_cache.py infra/docker-compose.yml
git commit -m "feat(search): add Redis cache backend and docker-compose service"
```

---

## Task 10: Implement Milvus vector_store

**Files:**
- Create: `backend/app/services/search/vector_store.py`

This module is mostly thin Milvus-SDK wrapping. Unit tests would mostly mock pymilvus, providing little value; coverage comes from Task 14's integration test.

- [ ] **Step 1: Implement vector_store**

`backend/app/services/search/vector_store.py`:

```python
from __future__ import annotations

import logging

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.core.config import settings
from app.services.search.exceptions import VectorStoreUnavailable

logger = logging.getLogger(__name__)

_CONNECTION_ALIAS = "default"


def connect() -> None:
    """Idempotently connect to Milvus using settings."""
    if connections.has_connection(_CONNECTION_ALIAS):
        return
    try:
        connections.connect(
            alias=_CONNECTION_ALIAS,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"connect failed: {e}") from e


def _image_schema() -> CollectionSchema:
    return CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("product_id", DataType.VARCHAR, max_length=36),
            FieldSchema("category_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("brand_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("image_idx", DataType.INT8),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.SEMANTIC_FGCLIP_DIM),
        ],
        description="One row per product image",
    )


def _text_schema() -> CollectionSchema:
    return CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema("category_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("brand_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.SEMANTIC_TEXT_DIM),
        ],
        description="One row per product description",
    )


def _index_params() -> dict:
    return {
        "index_type": settings.SEMANTIC_MILVUS_INDEX_TYPE,
        "metric_type": "IP",
        "params": {"nlist": settings.SEMANTIC_MILVUS_NLIST},
    }


def ensure_collections(*, drop: bool = False) -> tuple[Collection, Collection]:
    connect()

    image_name = settings.SEMANTIC_COLLECTION_IMAGE
    text_name = settings.SEMANTIC_COLLECTION_TEXT

    if drop:
        for name in (image_name, text_name):
            if utility.has_collection(name):
                utility.drop_collection(name)

    if not utility.has_collection(image_name):
        coll = Collection(image_name, schema=_image_schema())
        coll.create_index(field_name="embedding", index_params=_index_params())
    if not utility.has_collection(text_name):
        coll = Collection(text_name, schema=_text_schema())
        coll.create_index(field_name="embedding", index_params=_index_params())

    image_coll = Collection(image_name)
    text_coll = Collection(text_name)
    image_coll.load()
    text_coll.load()
    return image_coll, text_coll


def upsert_image_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    """rows: list of {id, product_id, category_id, brand_id, image_idx, embedding}."""
    if not rows:
        return
    try:
        coll.upsert(rows)
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image upsert failed: {e}") from e


def upsert_text_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    if not rows:
        return
    try:
        coll.upsert(rows)
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text upsert failed: {e}") from e


def flush(coll: Collection) -> None:
    coll.flush()


def search_image(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    expr: str | None,
) -> list[tuple[str, str, float]]:
    """Return list of (image_id, product_id, score) sorted by score desc."""
    try:
        results = coll.search(
            data=[query.tolist()],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": settings.SEMANTIC_MILVUS_NPROBE}},
            limit=top_k,
            expr=expr,
            output_fields=["product_id"],
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image search failed: {e}") from e

    out: list[tuple[str, str, float]] = []
    for hit in results[0]:
        out.append((hit.id, hit.entity.get("product_id"), float(hit.score)))
    return out


def search_text(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    expr: str | None,
) -> list[tuple[str, float]]:
    """Return list of (product_id, score) sorted by score desc."""
    try:
        results = coll.search(
            data=[query.tolist()],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": settings.SEMANTIC_MILVUS_NPROBE}},
            limit=top_k,
            expr=expr,
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text search failed: {e}") from e

    return [(hit.id, float(hit.score)) for hit in results[0]]


def build_filter_expr(
    *, category_ids: list[str] | None, brand_ids: list[str] | None
) -> str | None:
    """Return a Milvus boolean expression or None.

    `brand_ids` here refers to the *resolved* brand_id list to filter on; the
    caller must have already converted brand_ids → category_ids if needed.
    """
    parts: list[str] = []
    if category_ids:
        ids = ", ".join(f'"{c}"' for c in category_ids)
        parts.append(f"category_id in [{ids}]")
    if brand_ids:
        ids = ", ".join(f'"{b}"' for b in brand_ids)
        parts.append(f"brand_id in [{ids}]")
    if not parts:
        return None
    return " and ".join(parts)
```

- [ ] **Step 2: Smoke import**

```bash
cd backend && ../backend/venv/bin/python -c "from app.services.search import vector_store; print('OK')"
```
Expected: `OK`. Note this does not connect to Milvus.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/search/vector_store.py
git commit -m "feat(search): Milvus client + collection schemas"
```

---

## Task 11: Implement BGE text embedder

**Files:**
- Create: `backend/app/services/search/embedders/bge.py`

- [ ] **Step 1: Implement BGE embedder**

`backend/app/services/search/embedders/bge.py`:

```python
from __future__ import annotations

import logging
import threading

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.search.embedders.base import TextEmbedder
from app.services.search.exceptions import EmbedderUnavailable

logger = logging.getLogger(__name__)


def _resolve_device() -> str:
    if settings.SEMANTIC_DEVICE == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return settings.SEMANTIC_DEVICE


class BgeTextEmbedder(TextEmbedder):
    _instance: "BgeTextEmbedder | None" = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "BgeTextEmbedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        try:
            self._model = SentenceTransformer(
                settings.SEMANTIC_TEXT_MODEL,
                device=_resolve_device(),
                cache_folder=settings.SEMANTIC_HF_CACHE_DIR,
            )
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"BGE load failed: {e}") from e

    @property
    def dim(self) -> int:
        return settings.SEMANTIC_TEXT_DIM

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        try:
            vecs = self._model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"BGE encode failed: {e}") from e
        return vecs.astype(np.float32, copy=False)
```

- [ ] **Step 2: Smoke import (does not load weights)**

```bash
cd backend && ../backend/venv/bin/python -c "from app.services.search.embedders.bge import BgeTextEmbedder; print('OK')"
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/search/embedders/bge.py
git commit -m "feat(search): BGE-small text embedder wrapper"
```

---

## Task 12: Implement FG-CLIP 2 embedder

**Files:**
- Create: `backend/app/services/search/embedders/fgclip.py`

- [ ] **Step 1: Implement FG-CLIP 2 wrapper**

`backend/app/services/search/embedders/fgclip.py`:

```python
from __future__ import annotations

import logging
import threading

import numpy as np
import torch
from PIL.Image import Image
from transformers import AutoModel, AutoProcessor

from app.core.config import settings
from app.services.search.embedders.base import ImageEmbedder, TextEmbedder
from app.services.search.embedders.bge import _resolve_device
from app.services.search.exceptions import EmbedderUnavailable

logger = logging.getLogger(__name__)


def _l2_normalize(x: torch.Tensor) -> torch.Tensor:
    return x / x.norm(dim=-1, keepdim=True).clamp(min=1e-12)


class FgClipEmbedder(ImageEmbedder, TextEmbedder):
    """Single FG-CLIP 2 model exposing both image and text encoding."""

    _instance: "FgClipEmbedder | None" = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "FgClipEmbedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        self._device = _resolve_device()
        try:
            self._processor = AutoProcessor.from_pretrained(
                settings.SEMANTIC_FGCLIP_MODEL,
                trust_remote_code=True,
                cache_dir=settings.SEMANTIC_HF_CACHE_DIR,
            )
            self._model = AutoModel.from_pretrained(
                settings.SEMANTIC_FGCLIP_MODEL,
                trust_remote_code=True,
                cache_dir=settings.SEMANTIC_HF_CACHE_DIR,
            ).to(self._device).eval()
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 load failed: {e}") from e

    @property
    def dim(self) -> int:
        return settings.SEMANTIC_FGCLIP_DIM

    @torch.inference_mode()
    def encode(self, items):  # type: ignore[override]
        # Dispatch for ABC: image list vs text list
        if not items:
            return np.zeros((0, self.dim), dtype=np.float32)
        if isinstance(items[0], str):
            return self._encode_text(items)
        return self._encode_image(items)

    @torch.inference_mode()
    def _encode_image(self, images: list[Image]) -> np.ndarray:
        try:
            inputs = self._processor(images=images, return_tensors="pt").to(self._device)
            feats = self._model.get_image_features(**inputs)
            feats = _l2_normalize(feats)
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 image encode failed: {e}") from e
        return feats.cpu().numpy().astype(np.float32, copy=False)

    @torch.inference_mode()
    def _encode_text(self, texts: list[str]) -> np.ndarray:
        try:
            inputs = self._processor(
                text=texts, return_tensors="pt", padding=True, truncation=True
            ).to(self._device)
            feats = self._model.get_text_features(**inputs)
            feats = _l2_normalize(feats)
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 text encode failed: {e}") from e
        return feats.cpu().numpy().astype(np.float32, copy=False)
```

- [ ] **Step 2: Smoke import**

```bash
cd backend && ../backend/venv/bin/python -c "from app.services.search.embedders.fgclip import FgClipEmbedder; print('OK')"
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/search/embedders/fgclip.py
git commit -m "feat(search): FG-CLIP 2 image+text embedder wrapper"
```

---

## Task 13: ML stack smoke test

**Files:**
- Create: `backend/scripts/check_ml_env.py`
- Modify: `Makefile`

- [ ] **Step 1: Write smoke script**

`backend/scripts/check_ml_env.py`:

```python
"""Smoke test the semantic-search ML stack.

Loads the BGE encoder and runs one forward pass to detect dependency
issues before reindexing or serving. Does not load FG-CLIP 2 (weights
heavy); a separate `--full` flag would be added in the future.
"""

import os
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    import numpy as np
    import torch
    import transformers
    import sentence_transformers
    import pymilvus

    print(f"python      = {sys.version.split()[0]}")
    print(f"torch       = {torch.__version__}, cuda={torch.cuda.is_available()}")
    print(f"transformers= {transformers.__version__}")
    print(f"sentence_t. = {sentence_transformers.__version__}")
    print(f"pymilvus    = {pymilvus.__version__}")
    print(f"numpy       = {np.__version__}")

    from sentence_transformers import SentenceTransformer

    model_id = os.environ.get("SEMANTIC_TEXT_MODEL", "BAAI/bge-small-en-v1.5")
    m = SentenceTransformer(model_id)
    v = m.encode(["hello world"])
    assert v.shape == (1, 384), f"unexpected shape {v.shape}"
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Add Makefile target**

Edit `Makefile`. Append before the final `seed:` target:

```makefile
# ── Semantic search ───────────────────────────────────────────────────────────

check-ml-env:
	cd backend && ../backend/venv/bin/python scripts/check_ml_env.py

install-ml-cpu:
	backend/venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
	backend/venv/bin/pip install -r backend/requirements-ml.txt

install-ml-gpu:
	backend/venv/bin/pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.5.1 torchvision==0.20.1
	backend/venv/bin/pip install -r backend/requirements-ml.txt
```

Also extend the `help:` block with the new lines (insert before the `Frontend` section):

```
	@echo ""
	@echo "Semantic Search"
	@echo "  make install-ml-cpu        Install PyTorch (CPU) and ML deps"
	@echo "  make install-ml-gpu        Install PyTorch (CUDA 12.4) and ML deps"
	@echo "  make check-ml-env          Smoke-test ML stack (loads BGE encoder)"
	@echo "  make reindex               Rebuild Milvus collections from MySQL products"
```

(`make reindex` will be wired in Task 17; included now to keep help coherent.)

- [ ] **Step 3: Run**

```bash
make check-ml-env
```
Expected: prints versions and `OK`. The first run downloads BGE weights (~130MB); subsequent runs are instant.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/check_ml_env.py Makefile
git commit -m "feat(search): ML stack smoke test + Makefile targets"
```

---

## Task 14: Implement search_service orchestrator with TDD

**Files:**
- Create: `backend/tests/search/test_search_service.py`
- Create: `backend/app/services/search/search_service.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/search/test_search_service.py`:

```python
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np

from app.services.search.search_service import semantic_search


class FakeCache:
    def __init__(self) -> None:
        self.store: dict = {}
        self.get_calls = 0
        self.set_calls = 0

    async def get(self, k):
        self.get_calls += 1
        return self.store.get(k)

    async def set(self, k, v, ttl):
        self.set_calls += 1
        self.store[k] = v

    async def clear(self):
        self.store.clear()


class SemanticSearchTest(unittest.TestCase):
    def _patches(
        self,
        *,
        image_results: list[tuple[str, str, float]],
        text_results: list[tuple[str, float]],
        cache: FakeCache,
    ):
        # Patch the lazy accessors used by semantic_search.
        bge = MagicMock()
        bge.encode.return_value = np.zeros((1, 384), dtype=np.float32)

        fg = MagicMock()
        fg.encode.return_value = np.zeros((1, 768), dtype=np.float32)

        return [
            patch(
                "app.services.search.search_service._get_text_embedder",
                return_value=bge,
            ),
            patch(
                "app.services.search.search_service._get_image_text_embedder",
                return_value=fg,
            ),
            patch(
                "app.services.search.search_service._search_image",
                return_value=image_results,
            ),
            patch(
                "app.services.search.search_service._search_text",
                return_value=text_results,
            ),
            patch(
                "app.services.search.search_service._get_cache",
                return_value=cache,
            ),
        ]

    def test_returns_ranked_full_after_fusion_and_outlier_cut(self) -> None:
        # 3 products: A (high both), B (mid), C (low) — C should be cut.
        image = [("img_A:0", "A", 0.95), ("img_B:0", "B", 0.7), ("img_C:0", "C", 0.2)]
        text = [("A", 0.9), ("B", 0.6), ("C", 0.1)]
        cache = FakeCache()
        with self._patches(image_results=image, text_results=text, cache=cache)[0], \
             self._patches(image_results=image, text_results=text, cache=cache)[1], \
             self._patches(image_results=image, text_results=text, cache=cache)[2], \
             self._patches(image_results=image, text_results=text, cache=cache)[3], \
             self._patches(image_results=image, text_results=text, cache=cache)[4]:
            ranked = asyncio.run(semantic_search("query", brand_ids=None, category_ids=None))
        self.assertGreaterEqual(len(ranked), 1)
        self.assertEqual(ranked[0][0], "A")
        self.assertNotIn("C", [pid for pid, _ in ranked])

    def test_cache_hit_skips_encoding(self) -> None:
        cache = FakeCache()
        # Pre-populate cache for the key the function will compute.
        from app.services.search.cache import make_cache_key

        key = make_cache_key("query", None, None)
        cache.store[key] = [("X", 1.0)]

        bge = MagicMock(); bge.encode.return_value = np.zeros((1, 384), dtype=np.float32)
        fg = MagicMock();  fg.encode.return_value = np.zeros((1, 768), dtype=np.float32)
        with patch("app.services.search.search_service._get_text_embedder", return_value=bge), \
             patch("app.services.search.search_service._get_image_text_embedder", return_value=fg), \
             patch("app.services.search.search_service._get_cache", return_value=cache), \
             patch("app.services.search.search_service._search_image") as si, \
             patch("app.services.search.search_service._search_text") as st:
            ranked = asyncio.run(semantic_search("query", brand_ids=None, category_ids=None))
        self.assertEqual(ranked, [("X", 1.0)])
        bge.encode.assert_not_called()
        fg.encode.assert_not_called()
        si.assert_not_called()
        st.assert_not_called()

    def test_empty_query_returns_empty_list(self) -> None:
        cache = FakeCache()
        ranked = asyncio.run(semantic_search("   ", brand_ids=None, category_ids=None))
        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, confirm failure**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_search_service -v
```
Expected: ImportError.

- [ ] **Step 3: Implement search_service**

`backend/app/services/search/search_service.py`:

```python
from __future__ import annotations

import asyncio
import logging

import numpy as np

from app.core.config import settings
from app.services.search.aggregator import aggregate_image_scores
from app.services.search.cache import (
    SearchCache,
    build_cache_from_settings,
    make_cache_key,
)
from app.services.search.fusion import fuse_and_filter

logger = logging.getLogger(__name__)

RankedList = list[tuple[str, float]]


# ── lazy accessors (patchable in tests) ─────────────────────────────────────

def _get_text_embedder():
    from app.services.search.embedders.bge import BgeTextEmbedder
    return BgeTextEmbedder.get()


def _get_image_text_embedder():
    from app.services.search.embedders.fgclip import FgClipEmbedder
    return FgClipEmbedder.get()


_cache_singleton: SearchCache | None = None


def _get_cache() -> SearchCache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = build_cache_from_settings()
    return _cache_singleton


def _search_image(query_vec: np.ndarray, expr: str | None) -> list[tuple[str, str, float]]:
    from app.services.search import vector_store

    image_coll, _ = vector_store.ensure_collections()
    return vector_store.search_image(
        image_coll,
        query=query_vec,
        top_k=settings.SEMANTIC_ANN_TOPN_IMAGE,
        expr=expr,
    )


def _search_text(query_vec: np.ndarray, expr: str | None) -> list[tuple[str, float]]:
    from app.services.search import vector_store

    _, text_coll = vector_store.ensure_collections()
    return vector_store.search_text(
        text_coll,
        query=query_vec,
        top_k=settings.SEMANTIC_ANN_TOPN_TEXT,
        expr=expr,
    )


# ── orchestrator ────────────────────────────────────────────────────────────

async def semantic_search(
    query: str,
    *,
    brand_ids: list[str] | None,
    category_ids: list[str] | None,
) -> RankedList:
    """Returns the ranked full list (post outlier cut) for the given query.

    Pagination, post-rank sort, and Product hydration are the caller's job.
    """
    if not query or not query.strip():
        return []

    cache = _get_cache()
    key = make_cache_key(query, brand_ids, category_ids)

    cached = await cache.get(key)
    if cached is not None:
        return cached

    # Build Milvus filter expression. brand_ids and category_ids here are
    # already-resolved scalar ID lists.
    from app.services.search.vector_store import build_filter_expr

    expr = build_filter_expr(category_ids=category_ids, brand_ids=brand_ids)

    # Encode (sync — encoders are CPU/GPU-bound, but each call is one short
    # forward pass; running them sequentially is fine for query latency).
    txt_embedder = _get_text_embedder()
    fg_embedder = _get_image_text_embedder()
    q_txt = txt_embedder.encode([query])[0]
    q_img = fg_embedder.encode([query])[0]

    # Run both ANN searches in parallel.
    loop = asyncio.get_running_loop()
    img_task = loop.run_in_executor(None, _search_image, q_img, expr)
    txt_task = loop.run_in_executor(None, _search_text, q_txt, expr)
    image_rows, text_rows = await asyncio.gather(img_task, txt_task)

    image_scores = aggregate_image_scores(
        image_rows, top_k=settings.SEMANTIC_IMAGE_AGG_TOP_K
    )
    text_scores = dict(text_rows)

    ranked = fuse_and_filter(
        image_scores=image_scores,
        text_scores=text_scores,
        alpha=settings.SEMANTIC_FUSION_ALPHA,
        tau=settings.SEMANTIC_OUTLIER_RATIO_TAU,
    )

    await cache.set(key, ranked, ttl=settings.SEMANTIC_CACHE_TTL_SEC)
    return ranked


async def clear_cache() -> None:
    cache = _get_cache()
    await cache.clear()
```

- [ ] **Step 4: Run tests, expect pass**

```bash
cd backend && ../backend/venv/bin/python -m unittest tests.search.test_search_service -v
```
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/search/search_service.py backend/tests/search/test_search_service.py
git commit -m "feat(search): semantic_search orchestrator with cache, fusion, outlier cut"
```

---

## Task 15: Wire search_service into product CRUD and endpoint

**Files:**
- Modify: `backend/app/crud/product.py`
- Modify: `backend/app/api/v1/endpoints/product.py`
- Modify: `backend/app/schemas/product.py` (add a tiny ranked-result helper if needed)

The endpoint signature stays identical; only the underlying ranking changes. When `search` is empty, the existing flow (filter + sort + paginate) is kept verbatim. When `search` is set, we route through `semantic_search`.

- [ ] **Step 1: Replace `_apply_search` with semantic dispatch**

In `backend/app/crud/product.py`, replace the `_apply_search` function and `search_products` body with the version below. The function signature remains the same so the endpoint does not change.

```python
import asyncio
import math
import random

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.search.search_service import semantic_search


PAGE_SIZE = 20
MAX_TOTAL = 500


def _post_sort_key(sort: str):
    if sort == "newest":
        return lambda p: p.created_at, True
    if sort == "price-high-low":
        return lambda p: p.price, True
    if sort == "price-low-high":
        return lambda p: p.price, False
    if sort == "discount-rate":
        return lambda p: p.discount, True
    return None


def _resolve_filter_ids(
    db: Session,
    *,
    brand_ids: list[str] | None,
    category_ids: list[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """Resolve brand_ids → category_id list, intersecting with category_ids."""
    final_cats = category_ids
    if brand_ids:
        rows = (
            db.query(Category.id)
            .filter(Category.brand_id.in_(brand_ids))
            .all()
        )
        cat_from_brand = [r[0] for r in rows]
        final_cats = (
            list(set(final_cats) & set(cat_from_brand)) if final_cats else cat_from_brand
        )
    return final_cats, None  # brand filter applied via category_ids


def _lexical_search(
    db: Session,
    *,
    brand_ids: list[str] | None,
    category_ids: list[str] | None,
    sort: str,
    page: int,
) -> dict:
    """No-query path: kept identical to the previous behavior."""
    base = db.query(Product)
    if category_ids:
        base = base.filter(Product.category_id.in_(category_ids))
    if brand_ids:
        base = base.join(Category, Product.category_id == Category.id).filter(
            Category.brand_id.in_(brand_ids)
        )

    total = min(base.count(), MAX_TOTAL)

    if sort == "newest":
        base = base.order_by(Product.created_at.desc())
    elif sort == "price-high-low":
        base = base.order_by(Product.price.desc())
    elif sort == "price-low-high":
        base = base.order_by(Product.price.asc())
    elif sort == "discount-rate":
        base = base.order_by(Product.discount.desc())

    max_page = max(math.ceil(total / PAGE_SIZE), 1)
    page = min(page, max_page)
    products = base.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

    available_brands = _facet_brands(db, category_ids)
    available_categories = _facet_categories(db, brand_ids)

    return {
        "products": products,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "available_brands": available_brands,
        "available_categories": available_categories,
    }


def _facet_brands(db: Session, category_ids: list[str] | None):
    q = db.query(Category.brand_id).distinct()
    if category_ids:
        q = q.filter(Category.id.in_(category_ids))
    brand_ids_present = [r[0] for r in q.all() if r[0] is not None]
    if not brand_ids_present:
        return []
    return db.query(Brand).filter(Brand.id.in_(brand_ids_present)).all()


def _facet_categories(db: Session, brand_ids: list[str] | None):
    q = db.query(Category)
    if brand_ids:
        q = q.filter(Category.brand_id.in_(brand_ids))
    return q.all()


def search_products(
    db: Session,
    search: str | None = None,
    brand_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    sort: str = "best-sellers",
    page: int = 1,
) -> dict:
    if not search or not search.strip():
        return _lexical_search(
            db,
            brand_ids=brand_ids,
            category_ids=category_ids,
            sort=sort,
            page=page,
        )

    resolved_cats, _ = _resolve_filter_ids(
        db, brand_ids=brand_ids, category_ids=category_ids
    )

    ranked = asyncio.run(
        semantic_search(
            search,
            brand_ids=None,            # already merged into resolved_cats
            category_ids=resolved_cats,
        )
    )

    if not ranked:
        return {
            "products": [],
            "total": 0,
            "page": 1,
            "page_size": PAGE_SIZE,
            "available_brands": [],
            "available_categories": [],
        }

    # Hydrate Product rows in ranked order.
    ranked_ids = [pid for pid, _ in ranked]
    rows = db.query(Product).filter(Product.id.in_(ranked_ids)).all()
    by_id = {p.id: p for p in rows}
    ordered: list[Product] = [by_id[pid] for pid in ranked_ids if pid in by_id]

    # Post-rank sort if user requested anything other than relevance.
    sort_spec = _post_sort_key(sort)
    if sort_spec is not None:
        key, reverse = sort_spec
        ordered = sorted(ordered, key=key, reverse=reverse)

    total = len(ordered)
    max_page = max(math.ceil(total / PAGE_SIZE), 1)
    page = min(page, max_page)
    page_products = ordered[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    # Facets from the candidate set.
    cand_cats = {p.category_id for p in ordered if p.category_id}
    cand_brands_q = (
        db.query(Category.brand_id)
        .filter(Category.id.in_(cand_cats))
        .distinct()
    )
    cand_brand_ids = [r[0] for r in cand_brands_q.all() if r[0] is not None]
    available_brands = (
        db.query(Brand).filter(Brand.id.in_(cand_brand_ids)).all()
        if cand_brand_ids
        else []
    )
    available_categories = (
        db.query(Category).filter(Category.id.in_(cand_cats)).all()
        if cand_cats
        else []
    )

    return {
        "products": page_products,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "available_brands": available_brands,
        "available_categories": available_categories,
    }
```

Keep the existing CRUD helpers (`create_product`, `get_product_by_id`, ..., `get_similar_products`) untouched; just add the imports and replace `search_products` + helpers above.

- [ ] **Step 2: Confirm endpoint already routes through `search_products`**

`backend/app/api/v1/endpoints/product.py` already calls `search_products(db, search=search, ...)`. Open the file and verify; no changes required if so. If `_apply_search` import remains, remove it.

- [ ] **Step 3: Map `SemanticSearchError` → 503 in the endpoint**

In `backend/app/api/v1/endpoints/product.py`, wrap the call inside `search()`:

```python
from app.services.search.exceptions import SemanticSearchError

@router.get("/search", response_model=ProductSearchResponse)
def search(
    search: str | None = Query(None),
    brand_ids: list[str] | None = Query(None),
    category_ids: list[str] | None = Query(None),
    page: int = Query(1, ge=1, le=25),
    sort: str = Query("best-sellers"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    try:
        result = search_products(
            db,
            search=search,
            brand_ids=brand_ids,
            category_ids=category_ids,
            sort=sort,
            page=page,
        )
    except SemanticSearchError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="semantic search temporarily unavailable",
        ) from e
    favorited_ids = (
        get_user_favorite_product_ids(db, current_user.id) if current_user else set()
    )
    result["products"] = [_to_product_out(p, favorited_ids) for p in result["products"]]
    return result
```

- [ ] **Step 4: Run existing test suite to confirm no regression on the lexical-empty path**

```bash
cd backend && ../backend/venv/bin/python -m unittest discover -s tests -v
```
Expected: existing tests still pass; new tests under `tests/search/` also pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/crud/product.py backend/app/api/v1/endpoints/product.py
git commit -m "feat(search): route /products/search through semantic_service when query present"
```

---

## Task 16: Implement reindex CLI

**Files:**
- Create: `backend/scripts/reindex_products.py`
- Modify: `Makefile`

- [ ] **Step 1: Implement script**

`backend/scripts/reindex_products.py`:

```python
"""Rebuild Milvus collections from MySQL Product rows.

Usage:
    python scripts/reindex_products.py [--rebuild] [--product-ids id1,id2]
        [--batch-size-products N] [--image-batch-size N]
        [--max-images-per-product N]
        [--skip-images] [--skip-descriptions]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.db.base  # noqa: F401 — register all models
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.services.search import vector_store
from app.services.search.embedders.bge import BgeTextEmbedder
from app.services.search.embedders.fgclip import FgClipEmbedder
from app.services.search.image_fetcher import fetch_images
from app.services.search.search_service import clear_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("reindex")


def _split_urls(raw: str | None, max_n: int) -> list[str]:
    if not raw:
        return []
    parts = [u.strip() for u in raw.split("|") if u.strip()]
    return parts[:max_n]


def _resolve_brand_id(db, category_id: str | None, cache: dict) -> str | None:
    if category_id is None:
        return None
    if category_id in cache:
        return cache[category_id]
    row = db.query(Category.brand_id).filter(Category.id == category_id).first()
    cache[category_id] = row[0] if row else None
    return cache[category_id]


async def _process_batch(
    products: list[Product],
    *,
    bge: BgeTextEmbedder,
    fg: FgClipEmbedder,
    args: argparse.Namespace,
    cat_to_brand: dict,
    db,
    image_coll,
    text_coll,
) -> tuple[int, int]:
    image_rows: list[dict] = []
    text_rows: list[dict] = []

    # Description embeddings (one batched call).
    if not args.skip_descriptions:
        desc_inputs = [(p.id, p.description) for p in products if p.description]
        if desc_inputs:
            descs = [d for _, d in desc_inputs]
            d_vecs = bge.encode(descs)
            for (pid, _), vec in zip(desc_inputs, d_vecs):
                p = next(p for p in products if p.id == pid)
                text_rows.append({
                    "id": p.id,
                    "category_id": p.category_id,
                    "brand_id": _resolve_brand_id(db, p.category_id, cat_to_brand),
                    "embedding": vec.tolist(),
                })

    # Image fetch + embed.
    if not args.skip_images:
        url_index: list[tuple[Product, int, str]] = []
        for p in products:
            urls = _split_urls(p.image, args.max_images_per_product)
            for idx, url in enumerate(urls):
                url_index.append((p, idx, url))

        if url_index:
            urls_only = [u for _, _, u in url_index]
            images = await fetch_images(
                urls_only,
                timeout_sec=settings.SEMANTIC_IMAGE_FETCH_TIMEOUT_SEC,
                retries=settings.SEMANTIC_IMAGE_FETCH_RETRIES,
                concurrency=settings.SEMANTIC_IMAGE_FETCH_CONCURRENCY,
            )
            kept: list[tuple[Product, int, object]] = [
                (p, idx, img) for (p, idx, _u), img in zip(url_index, images)
                if img is not None
            ]

            for start in range(0, len(kept), args.image_batch_size):
                batch = kept[start : start + args.image_batch_size]
                imgs = [img for _, _, img in batch]
                vecs = fg.encode(imgs)
                for (p, idx, _img), vec in zip(batch, vecs):
                    image_rows.append({
                        "id": f"{p.id}:{idx}",
                        "product_id": p.id,
                        "category_id": p.category_id,
                        "brand_id": _resolve_brand_id(db, p.category_id, cat_to_brand),
                        "image_idx": idx,
                        "embedding": vec.tolist(),
                    })

    if image_rows:
        vector_store.upsert_image_rows(image_coll, image_rows)
    if text_rows:
        vector_store.upsert_text_rows(text_coll, text_rows)
    return len(image_rows), len(text_rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size-products", type=int, default=settings.SEMANTIC_INDEX_BATCH_PRODUCTS)
    p.add_argument("--image-batch-size", type=int, default=settings.SEMANTIC_INDEX_BATCH_IMAGES)
    p.add_argument("--max-images-per-product", type=int, default=settings.SEMANTIC_MAX_IMAGES_PER_PRODUCT)
    p.add_argument("--product-ids", type=str, default=None,
                   help="comma-separated product IDs to reindex (default: all)")
    p.add_argument("--skip-images", action="store_true")
    p.add_argument("--skip-descriptions", action="store_true")
    p.add_argument("--rebuild", action="store_true",
                   help="drop and recreate collections before insert")
    return p.parse_args()


async def amain(args: argparse.Namespace) -> int:
    image_coll, text_coll = vector_store.ensure_collections(drop=args.rebuild)
    bge = BgeTextEmbedder.get()
    fg = FgClipEmbedder.get()

    db = SessionLocal()
    try:
        q = db.query(Product)
        if args.product_ids:
            ids = [s.strip() for s in args.product_ids.split(",") if s.strip()]
            q = q.filter(Product.id.in_(ids))
        all_products = q.all()
    finally:
        db.close()

    log.info("indexing %d products", len(all_products))
    cat_to_brand: dict = {}
    total_images = total_texts = 0
    started = time.time()

    for start in range(0, len(all_products), args.batch_size_products):
        batch = all_products[start : start + args.batch_size_products]
        db = SessionLocal()
        try:
            n_img, n_txt = await _process_batch(
                batch,
                bge=bge, fg=fg,
                args=args, cat_to_brand=cat_to_brand, db=db,
                image_coll=image_coll, text_coll=text_coll,
            )
            total_images += n_img
            total_texts += n_txt
        finally:
            db.close()

        done = start + len(batch)
        if done % 100 == 0 or done == len(all_products):
            elapsed = time.time() - started
            log.info(
                "progress %d/%d | images=%d texts=%d | %.1fs",
                done, len(all_products), total_images, total_texts, elapsed,
            )

    vector_store.flush(image_coll)
    vector_store.flush(text_coll)
    await clear_cache()
    log.info("done. images=%d texts=%d", total_images, total_texts)
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Wire `make reindex`**

Edit `Makefile`. Append after the `install-ml-gpu:` target:

```makefile
reindex:
	cd backend && ../backend/venv/bin/python scripts/reindex_products.py
```

- [ ] **Step 3: Smoke run on a tiny subset**

Pick 2 product IDs from MySQL:

```bash
backend/venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models.product import Product
db = SessionLocal()
ids = [p.id for p in db.query(Product).limit(2).all()]
print(','.join(ids))
"
```

Then run:
```bash
cd backend && ../backend/venv/bin/python scripts/reindex_products.py --rebuild --product-ids "<id1>,<id2>"
```

Expected: "indexing 2 products", progress log, "done. images=N texts=2".

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/reindex_products.py Makefile
git commit -m "feat(search): reindex CLI for Milvus collections"
```

---

## Task 17: Documentation

**Files:**
- Create: `docs/features/search/overview.md`
- Create: `docs/features/search/architecture.md`
- Create: `docs/features/search/flows.md`
- Modify: `docs/index/feature-map.md`

- [ ] **Step 1: Write `overview.md`**

`docs/features/search/overview.md`:

```markdown
---
feature: search
doc_type: overview
tags: [semantic-search, milvus, fg-clip2, bge-small, embeddings]
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
(no Milvus call, no encoding).

## Where things live

| Concern | File |
|---|---|
| Orchestrator | `app/services/search/search_service.py` |
| Image encoder + text-side encoder for image | `app/services/search/embedders/fgclip.py` |
| Description encoder | `app/services/search/embedders/bge.py` |
| Milvus client + schemas | `app/services/search/vector_store.py` |
| Image download | `app/services/search/image_fetcher.py` |
| Score aggregation (top-K mean) | `app/services/search/aggregator.py` |
| Score fusion + outlier cut | `app/services/search/fusion.py` |
| Result cache (memory or Redis) | `app/services/search/cache.py` |
| Indexing CLI | `scripts/reindex_products.py` |

## Tunable settings

All parameters live on `Settings` (env-driven). The most useful ones:

| Env | Default | Effect |
|---|---|---|
| `SEMANTIC_FUSION_ALPHA` | `0.5` | image weight; text = 1−α |
| `SEMANTIC_OUTLIER_RATIO_TAU` | `0.6` | drop items below τ × top1 |
| `SEMANTIC_IMAGE_AGG_TOP_K` | `3` | mean of K best images per product |
| `SEMANTIC_ANN_TOPN_IMAGE` | `500` | ANN limit, image side |
| `SEMANTIC_ANN_TOPN_TEXT` | `500` | ANN limit, text side |
| `SEMANTIC_CACHE_BACKEND` | `memory` | `memory` or `redis` |

Changing these does not require reindexing. Changing models or collection
names does (build a `_v2` collection and flip).
```

- [ ] **Step 2: Write `architecture.md`**

`docs/features/search/architecture.md`:

```markdown
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
```

- [ ] **Step 3: Write `flows.md`**

`docs/features/search/flows.md`:

```markdown
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
```

- [ ] **Step 4: Add search to `feature-map.md`**

Edit `docs/index/feature-map.md`. Insert a new section before the `setup / architecture` section:

```markdown
---

## search
**Keywords:** semantic search, embeddings, FG-CLIP, FG-CLIP2, BGE, Milvus, vector search, similarity, image embedding, description embedding, ANN, reindex, top-K aggregation, fusion, outlier cut, cache, Redis

| Question type | Read |
|---|---|
| How does search work overall? | `docs/features/search/overview.md` |
| What Milvus collections and schemas exist? | `docs/features/search/architecture.md` |
| What is the query / indexing pipeline? | `docs/features/search/flows.md` |
| How do I rebuild the vector index? | `docs/features/search/flows.md` |
| Which env vars tune ranking? | `docs/features/search/overview.md` |
```

- [ ] **Step 5: Commit**

```bash
git add docs/features/search/ docs/index/feature-map.md
git commit -m "docs(search): overview, architecture, flows + feature-map entry"
```

---

## Task 18: End-to-end manual verification

**Files:** none (verification only). If small fixes are needed, commit them at the end.

- [ ] **Step 1: Boot infra**

```bash
make docker-up
```

Wait until Milvus and Redis are healthy:
```bash
docker compose -f infra/docker-compose.yml ps
```
Expected: `shope_mysql`, `shope_milvus`, `shope_redis`, `shope_etcd`, `shope_minio` all `Up (healthy)` or `Up`.

- [ ] **Step 2: Reindex on a small sample**

Pick 50 product IDs:
```bash
backend/venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models.product import Product
db = SessionLocal()
print(','.join(p.id for p in db.query(Product).limit(50).all()))
" > /tmp/sample_ids.txt
```

Run:
```bash
cd backend && ../backend/venv/bin/python scripts/reindex_products.py \
  --rebuild --product-ids "$(cat /tmp/sample_ids.txt)"
```

Expected: completes without error; Milvus has rows in both collections.

- [ ] **Step 3: Boot backend and query**

```bash
make run-backend
```

In another terminal:
```bash
curl 'http://localhost:8000/products/search?search=running+shoes&page=1' | head -c 500
```

Expected: JSON `ProductSearchResponse` with `products` non-empty, `total > 0`.

- [ ] **Step 4: Cache-hit test**

Run the same curl twice. The second should return in <50 ms (vs hundreds on first call).

```bash
time curl -s 'http://localhost:8000/products/search?search=running+shoes' > /dev/null
time curl -s 'http://localhost:8000/products/search?search=running+shoes' > /dev/null
```

- [ ] **Step 5: Filter test**

```bash
curl 'http://localhost:8000/products/search?search=jacket&brand_ids=<known_brand_id>'
```

Expected: every product returned has the expected brand.

- [ ] **Step 6: Empty-query path unchanged**

```bash
curl 'http://localhost:8000/products/search?page=1' | head -c 500
```

Expected: returns the same shape as the previous (lexical) implementation
(unfiltered listing, page 1).

- [ ] **Step 7: Run the full unit test suite**

```bash
cd backend && ../backend/venv/bin/python -m unittest discover -s tests -v
```

Expected: all tests pass. If anything regresses, fix and add a final commit:

```bash
git add -p
git commit -m "fix(search): <specific fix>"
```

---

## Self-Review

**1. Spec coverage check**

| Spec section | Plan task |
|---|---|
| §3 Models | Tasks 11 (BGE), 12 (FG-CLIP 2), Task 1 (deps) |
| §4 Architecture & module layout | Tasks 3–14 (each module) |
| §5 Milvus schema | Task 10 |
| §6 Indexing pipeline | Task 16 |
| §7 Query pipeline (steps [0]–[8]) | Task 14 (orchestrator) + Task 15 (CRUD wiring) |
| §8 Cache | Tasks 8, 9 |
| §9 Configuration surface | Task 2 |
| §10 Dependencies & version pinning | Task 1 + Task 13 |
| §11 Error handling (exception hierarchy, 503 mapping, cache fail-soft) | Task 3, Task 9 (fail-soft), Task 15 (503 mapping) |
| §12 Testing | Tasks 5, 6, 7, 8, 9, 14 |
| §13 Open issues / future work | covered as non-goals; no task |
| §2 Non-goals | respected (no image-query, no auto-incremental, English only) |

No gaps.

**2. Placeholder scan**

No "TBD", "TODO", "implement later". Each step has actual code. The
verification checklist in Task 18 prescribes specific commands and
expected outcomes.

**3. Type / signature consistency**

- `aggregate_image_scores(rows, top_k)` consumed in Task 14 with `top_k=settings.SEMANTIC_IMAGE_AGG_TOP_K`. Signature matches Task 5.
- `fuse_and_filter(image_scores, text_scores, alpha, tau)` in Task 14 matches Task 6.
- `fetch_images(urls, timeout_sec, retries, concurrency)` in Task 16 matches Task 7.
- `make_cache_key(query, brand_ids, category_ids)` consumed in Task 14; matches Task 8.
- `SearchCache` protocol methods `get` / `set` / `clear` are async; consumers in Task 14 use `await`. Consistent.
- `vector_store.search_image` returns `list[(image_id, product_id, score)]`; `aggregate_image_scores` expects exactly this triple shape.
- `vector_store.search_text` returns `list[(product_id, score)]`; consumed via `dict(text_rows)` in Task 14.
- `semantic_search(query, *, brand_ids, category_ids)` keyword-only → callers in Task 15 pass them as keywords.

All consistent.
