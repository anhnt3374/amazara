from __future__ import annotations

import asyncio
import io
import logging
from collections import Counter

import aiohttp
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


# Browser-like default headers. Many CDN providers (Cloudflare, Akamai, the
# Zara / Nike / etc. image servers) reject requests with empty or default
# `Python/aiohttp` User-Agent and return 403. Posing as a recent Chrome
# avoids most of those blocks.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# 4xx codes that are permanent — retrying won't help.
_PERMANENT_4XX = frozenset({400, 401, 403, 404, 410, 451})


async def _fetch_one(
    session: aiohttp.ClientSession,
    url: str,
    timeout_sec: int,
    retries: int,
    status_counter: Counter[str] | None = None,
) -> Image.Image | None:
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status in _PERMANENT_4XX:
                    if status_counter is not None:
                        status_counter[f"http_{resp.status}"] += 1
                    logger.info(
                        "image fetch %s → %d (permanent, no retry)",
                        url,
                        resp.status,
                    )
                    return None
                if resp.status >= 400:
                    # Transient (5xx, 429) — retry
                    raise RuntimeError(f"HTTP {resp.status}")
                data = await resp.read()
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
                if status_counter is not None:
                    status_counter["ok"] += 1
                return img.convert("RGB")
            except (UnidentifiedImageError, OSError) as e:
                if status_counter is not None:
                    status_counter["decode_error"] += 1
                logger.warning("image decode failed for %s: %s", url, e)
                return None
        except Exception as e:  # noqa: BLE001 — retry on any network error
            last_error = e
            if attempt < retries:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
    if status_counter is not None:
        status_counter["network_error"] += 1
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
    is expected to skip them. Order is preserved. Logs a summary of outcomes
    at INFO level so reindex callers can see how many fetches failed and why.
    """
    if not urls:
        return []
    sem = asyncio.Semaphore(concurrency)
    status_counter: Counter[str] = Counter()

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        async def _bound(url: str) -> Image.Image | None:
            async with sem:
                return await _fetch_one(
                    session, url, timeout_sec, retries, status_counter
                )

        results = await asyncio.gather(*(_bound(u) for u in urls))

    if status_counter:
        summary = ", ".join(f"{k}={v}" for k, v in sorted(status_counter.items()))
        logger.info("image fetch summary: total=%d (%s)", len(urls), summary)

    return results
