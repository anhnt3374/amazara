"""Seed products from products.json into the database.

Requires stores to be seeded first (seed_stores.py).
Also creates brands and categories on the fly from the JSON data.
Each product is randomly assigned to one of the existing stores.
"""

import json
import math
import os
import random
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401 — register all models before any query
from app.db.session import SessionLocal
from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.store import Store

MOCK_DIR = os.path.dirname(__file__)
PRODUCTS_JSON = os.path.join(MOCK_DIR, "products.json")


INR_TO_USD = 84.0


def parse_price(raw) -> int:
    """Convert price to integer USD.

    Handles:
      - float/int (already USD): 40.0 → 40
      - string with ₹ (INR): "₹ 4,990.00" → round(4990 / 84) = 59
    """
    if isinstance(raw, (int, float)):
        return int(raw)
    text = str(raw)
    is_inr = "₹" in text
    text = text.replace("₹", "").replace(",", "").strip()
    try:
        value = float(text)
    except (ValueError, TypeError):
        return 0
    if is_inr:
        value = value / INR_TO_USD
    return round(value)


def clean_image(raw) -> str | None:
    """Return image URL or None if the value is NaN / empty."""
    if isinstance(raw, float) and math.isnan(raw):
        return None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()[:500]
    return None


def main():
    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        products_data = json.load(f)

    print(f"Loaded {len(products_data)} products from {PRODUCTS_JSON}")

    db = SessionLocal()

    # Fetch all stores — abort if none exist
    store_ids = [s.id for s in db.query(Store.id).all()]
    if not store_ids:
        print("ERROR: No stores found. Run seed_stores.py first.")
        db.close()
        sys.exit(1)
    print(f"Found {len(store_ids)} stores to assign products to.")

    # Caches for brand and category lookups
    brand_cache: dict[str, str] = {}   # name → id
    cat_cache: dict[tuple[str, str | None], str] = {}  # (name, brand_id) → id

    for brand in db.query(Brand).all():
        brand_cache[brand.name] = brand.id
    for cat in db.query(Category).all():
        cat_cache[(cat.name, cat.brand_id)] = cat.id

    created = 0
    skipped = 0

    try:
        for item in products_data:
            name = item.get("name", "").strip()
            if not name:
                skipped += 1
                continue

            # Brand
            brand_name = (item.get("brand") or "").strip()
            brand_id = None
            if brand_name:
                if brand_name not in brand_cache:
                    brand = Brand(name=brand_name)
                    db.add(brand)
                    db.flush()
                    brand_cache[brand_name] = brand.id
                brand_id = brand_cache[brand_name]

            # Category
            cat_name = (item.get("category") or "").strip()
            category_id = None
            if cat_name:
                cat_key = (cat_name, brand_id)
                if cat_key not in cat_cache:
                    category = Category(name=cat_name, brand_id=brand_id)
                    db.add(category)
                    db.flush()
                    cat_cache[cat_key] = category.id
                category_id = cat_cache[cat_key]

            product = Product(
                name=name[:255],
                description=item.get("description"),
                price=parse_price(item.get("price", 0)),
                discount=int(item.get("discount", 0)),
                image=clean_image(item.get("images")),
                low_tier=0,
                category_id=category_id,
                store_id=random.choice(store_ids),
            )
            db.add(product)
            created += 1

            if created % 500 == 0:
                db.commit()
                print(f"  Created {created} products...")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"\nDone! Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
