from __future__ import annotations

import hashlib
import logging
import time
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
