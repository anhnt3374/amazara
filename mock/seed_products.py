"""Seed products from products_clean.json into the database.

Requires stores to be seeded first (seed_stores.py) and requires the
validation step (validate_products.py) to have produced products_clean.json.
Brands and categories are created on the fly from the JSON data.
Each product is randomly assigned to one of the existing stores.
Exports products.csv with one row per seeded product.
"""

import csv
import json
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
PRODUCTS_JSON = os.path.join(MOCK_DIR, "products_clean.json")
PRODUCTS_CSV = os.path.join(MOCK_DIR, "products.csv")

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


def main():
    if not os.path.exists(PRODUCTS_JSON):
        print(f"ERROR: {PRODUCTS_JSON} not found. Run validate_products.py first.")
        sys.exit(1)

    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        products_data = json.load(f)

    print(f"Loaded {len(products_data)} products from {PRODUCTS_JSON}")

    db = SessionLocal()

    store_ids = [s.id for s in db.query(Store.id).all()]
    if not store_ids:
        print("ERROR: No stores found. Run seed_stores.py first.")
        db.close()
        sys.exit(1)
    print(f"Found {len(store_ids)} stores to assign products to.")

    brand_cache: dict[str, str] = {}
    cat_cache: dict[tuple[str, str | None], str] = {}

    for brand in db.query(Brand).all():
        brand_cache[brand.name] = brand.id
    for cat in db.query(Category).all():
        cat_cache[(cat.name, cat.brand_id)] = cat.id

    created = 0
    skipped = 0
    csv_rows: list[dict] = []

    try:
        for item in products_data:
            name = (item.get("name") or "").strip()
            if not name:
                skipped += 1
                continue

            brand_name = (item.get("brand") or "").strip()
            brand_id = None
            if brand_name:
                if brand_name not in brand_cache:
                    brand = Brand(name=brand_name)
                    db.add(brand)
                    db.flush()
                    brand_cache[brand_name] = brand.id
                brand_id = brand_cache[brand_name]

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

            image = (item.get("images") or "").strip() or None
            store_id = random.choice(store_ids)
            stock = int(item.get("quantity") or 0)
            price = parse_price(item.get("price", 0))
            discount = int(item.get("discount", 0))

            product = Product(
                name=name[:255],
                description=item.get("description"),
                price=price,
                discount=discount,
                image=image,
                stock=stock,
                category_id=category_id,
                store_id=store_id,
            )
            db.add(product)
            db.flush()

            csv_rows.append({
                "id": product.id,
                "name": product.name,
                "brand": brand_name or "",
                "category": cat_name or "",
                "store_id": store_id,
                "price": price,
                "discount": discount,
                "stock": stock,
                "image_count": len([u for u in (image or "").split("|") if u.strip()]),
                "image_first": (image or "").split("|")[0].strip() if image else "",
            })

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

    with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "name", "brand", "category", "store_id",
                "price", "discount", "stock", "image_count", "image_first",
            ],
        )
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)

    print(f"\nDone! Created: {created}, Skipped: {skipped}")
    print(f"Products saved to: {PRODUCTS_CSV}")


if __name__ == "__main__":
    main()
