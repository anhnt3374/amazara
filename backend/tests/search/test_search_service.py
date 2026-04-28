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
        fg.encode.return_value = np.zeros((1, 512), dtype=np.float32)

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
        ps = self._patches(image_results=image, text_results=text, cache=cache)
        with ps[0], ps[1], ps[2], ps[3], ps[4]:
            ranked = asyncio.run(semantic_search("query", brand_ids=None, category_ids=None))
        self.assertGreaterEqual(len(ranked), 1)
        self.assertEqual(ranked[0][0], "A")
        self.assertNotIn("C", [pid for pid, _ in ranked])

    def test_cache_hit_skips_encoding(self) -> None:
        cache = FakeCache()
        from app.services.search.cache import make_cache_key

        key = make_cache_key("query", None, None)
        cache.store[key] = [("X", 1.0)]

        bge = MagicMock(); bge.encode.return_value = np.zeros((1, 384), dtype=np.float32)
        fg = MagicMock();  fg.encode.return_value = np.zeros((1, 512), dtype=np.float32)
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
        ranked = asyncio.run(semantic_search("   ", brand_ids=None, category_ids=None))
        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
