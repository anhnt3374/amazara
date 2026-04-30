"""Rebuild Weaviate collections from PostgreSQL Product rows.

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
    bge = BgeTextEmbedder.get() if not args.skip_descriptions else None
    fg = FgClipEmbedder.get() if not args.skip_images else None

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
