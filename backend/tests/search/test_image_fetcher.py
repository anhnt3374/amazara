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
