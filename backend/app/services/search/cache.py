from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Iterable
from typing import Protocol

from cachetools import TTLCache
import redis.asyncio as aioredis

from app.services.search.exceptions import CacheUnavailable

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
    """Per-entry TTL cache. cachetools.TTLCache uses one TTL for the whole
    cache; we need per-entry, so this stores expiry timestamps alongside
    values in a TTLCache that holds a generous outer TTL.
    """

    def __init__(self, max_entries: int, default_ttl_sec: int) -> None:
        # Outer TTL is large; per-entry expiry stored as a tuple.
        self._cache: TTLCache = TTLCache(
            maxsize=max_entries,
            ttl=max(default_ttl_sec, 86400),
        )
        self._default_ttl = default_ttl_sec

    async def get(self, key: str) -> RankedList | None:
        item = self._cache.get(key)
        if item is None:
            return None
        value, expires_at = item
        if time.monotonic() >= expires_at:
            self._cache.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: RankedList, ttl: int) -> None:
        expires_at = time.monotonic() + max(ttl, 0)
        self._cache[key] = (value, expires_at)

    async def clear(self) -> None:
        self._cache.clear()


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
