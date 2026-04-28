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
