from __future__ import annotations

import asyncio
import logging
import time

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


def _search_image(query_vec: np.ndarray, filters) -> list[tuple[str, str, float]]:
    from app.services.search import vector_store

    image_coll, _ = vector_store.ensure_collections()
    return vector_store.search_image(
        image_coll,
        query=query_vec,
        top_k=settings.SEMANTIC_ANN_TOPN_IMAGE,
        filters=filters,
    )


def _search_text(query_vec: np.ndarray, filters) -> list[tuple[str, float]]:
    from app.services.search import vector_store

    _, text_coll = vector_store.ensure_collections()
    return vector_store.search_text(
        text_coll,
        query=query_vec,
        top_k=settings.SEMANTIC_ANN_TOPN_TEXT,
        filters=filters,
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

    t_start = time.perf_counter()

    cache = _get_cache()
    key = make_cache_key(query, brand_ids, category_ids)

    t0 = time.perf_counter()
    cached = await cache.get(key)
    cache_get_ms = (time.perf_counter() - t0) * 1000
    if cached is not None:
        logger.info(
            "semantic_search query=%r hit=cache total=%.1fms cache_get=%.1fms results=%d",
            query,
            (time.perf_counter() - t_start) * 1000,
            cache_get_ms,
            len(cached),
        )
        return cached

    # Build Weaviate filter object. brand_ids and category_ids here are
    # already-resolved scalar ID lists.
    from app.services.search.vector_store import build_filter_expr

    filters = build_filter_expr(category_ids=category_ids, brand_ids=brand_ids)

    # Encode (sync — encoders are CPU/GPU-bound, but each call is one short
    # forward pass; running them sequentially is fine for query latency).
    txt_embedder = _get_text_embedder()
    fg_embedder = _get_image_text_embedder()

    t0 = time.perf_counter()
    q_txt = txt_embedder.encode([query])[0]
    embed_text_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    q_img = fg_embedder.encode([query])[0]
    embed_image_ms = (time.perf_counter() - t0) * 1000

    # Run both ANN searches in parallel; time each independently.
    loop = asyncio.get_running_loop()

    async def _timed(awaitable):
        t = time.perf_counter()
        res = await awaitable
        return res, (time.perf_counter() - t) * 1000

    (image_rows, ann_image_ms), (text_rows, ann_text_ms) = await asyncio.gather(
        _timed(loop.run_in_executor(None, _search_image, q_img, filters)),
        _timed(loop.run_in_executor(None, _search_text, q_txt, filters)),
    )

    t0 = time.perf_counter()
    image_scores = aggregate_image_scores(
        image_rows, top_k=settings.SEMANTIC_IMAGE_AGG_TOP_K
    )
    text_scores = dict(text_rows)
    aggregate_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    ranked = fuse_and_filter(
        image_scores=image_scores,
        text_scores=text_scores,
        alpha=settings.SEMANTIC_FUSION_ALPHA,
        tau=settings.SEMANTIC_OUTLIER_RATIO_TAU,
    )
    fuse_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    await cache.set(key, ranked, ttl=settings.SEMANTIC_CACHE_TTL_SEC)
    cache_set_ms = (time.perf_counter() - t0) * 1000

    total_ms = (time.perf_counter() - t_start) * 1000
    logger.info(
        "semantic_search query=%r hit=miss total=%.1fms "
        "cache_get=%.1f embed_text=%.1f embed_image=%.1f "
        "ann_image=%.1f(rows=%d) ann_text=%.1f(rows=%d) "
        "aggregate=%.1f fuse=%.1f cache_set=%.1f results=%d",
        query,
        total_ms,
        cache_get_ms,
        embed_text_ms,
        embed_image_ms,
        ann_image_ms,
        len(image_rows),
        ann_text_ms,
        len(text_rows),
        aggregate_ms,
        fuse_ms,
        cache_set_ms,
        len(ranked),
    )
    return ranked


async def clear_cache() -> None:
    cache = _get_cache()
    await cache.clear()


async def aclose_cache() -> None:
    global _cache_singleton
    cache, _cache_singleton = _cache_singleton, None
    if cache is not None:
        await cache.aclose()
