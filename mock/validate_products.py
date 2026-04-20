"""Validate image URLs in products.json.

Reads mock/products.json, splits each `images` field on " | ", performs
parallel HEAD checks with a 5-second timeout, and writes:
- mock/products_clean.json  — only products with at least one reachable URL
  (its `images` field rewritten to contain only valid URLs, pipe-joined)
- mock/url_check_cache.json — { url: bool } lookup for resumability
"""

import asyncio
import json
import os
import sys
import time

import aiohttp

HERE = os.path.dirname(__file__)
INPUT_FILE = os.path.join(HERE, "products.json")
OUTPUT_FILE = os.path.join(HERE, "products_clean.json")
CACHE_FILE = os.path.join(HERE, "url_check_cache.json")

CONCURRENCY = 50
TIMEOUT_SECONDS = 5
PROGRESS_EVERY = 500


def load_cache() -> dict[str, bool]:
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache: dict[str, bool]) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def split_urls(raw: object) -> list[str]:
    if not isinstance(raw, str):
        return []
    return [u.strip() for u in raw.split("|") if u.strip()]


async def check_url(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
) -> tuple[str, bool]:
    async with sem:
        try:
            async with session.head(url, allow_redirects=True) as resp:
                return url, 200 <= resp.status < 400
        except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeError, ValueError):
            return url, False


async def validate_urls(urls: list[str], cache: dict[str, bool]) -> dict[str, bool]:
    pending = [u for u in urls if u not in cache]
    if not pending:
        return cache

    print(f"Checking {len(pending)} uncached URLs (cache has {len(cache)})...")
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [check_url(session, sem, u) for u in pending]
        done_count = 0
        start = time.time()
        for coro in asyncio.as_completed(tasks):
            url, ok = await coro
            cache[url] = ok
            done_count += 1
            if done_count % PROGRESS_EVERY == 0:
                elapsed = time.time() - start
                rate = done_count / elapsed if elapsed else 0
                print(
                    f"  {done_count}/{len(pending)} checked "
                    f"({rate:.1f} urls/sec, {int(elapsed)}s elapsed)"
                )
                save_cache(cache)

    save_cache(cache)
    return cache


def main() -> None:
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found.")
        sys.exit(1)

    print(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)
    print(f"  {len(products)} products.")

    unique_urls: set[str] = set()
    for p in products:
        for u in split_urls(p.get("images")):
            unique_urls.add(u)
    print(f"  {len(unique_urls)} unique image URLs.")

    cache = load_cache()
    cache = asyncio.run(validate_urls(list(unique_urls), cache))

    dead_urls = sum(1 for ok in cache.values() if not ok)
    print(f"\nValidation complete: {dead_urls}/{len(cache)} dead URLs.")

    kept: list[dict] = []
    dropped = 0
    for p in products:
        valid = [u for u in split_urls(p.get("images")) if cache.get(u, False)]
        if not valid:
            dropped += 1
            continue
        p = dict(p)
        p["images"] = " | ".join(valid)
        kept.append(p)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(
        f"\nDone! Kept {len(kept)}, dropped {dropped} products. "
        f"Wrote {OUTPUT_FILE}."
    )


if __name__ == "__main__":
    main()
