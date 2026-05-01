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


class RedisCacheLoopBindingTest(unittest.TestCase):
    def test_conn_rebinds_when_event_loop_changes(self) -> None:
        # Regression: a single RedisCache instance reused across two
        # asyncio.run() calls must not return a client whose underlying
        # transport was closed by the first loop.
        from app.services.search.cache import RedisCache

        cache = RedisCache("redis://localhost:1/0")

        async def get_client():
            return await cache._conn()

        client_1 = asyncio.run(get_client())
        client_2 = asyncio.run(get_client())

        self.assertIsNot(client_1, client_2)


if __name__ == "__main__":
    unittest.main()
