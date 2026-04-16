"""Seed 100–500 mock reviews per product using the sentiment sample pool.

Requires users and products to be seeded first.
Reviews are drawn from generic_review_sentiment_1200.json and assigned
random users. The label field in the JSON is ignored (the Review model
has no rating column) — it only guided the tone of each review text.
"""

import json
import os
import random
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401 — register all models before any query
from app.db.session import engine
from app.models.base import generate_uuid
from app.models.product import Product
from app.models.user import User

from sqlalchemy import text
from sqlalchemy.orm import Session

MOCK_DIR = os.path.dirname(__file__)
REVIEWS_JSON = os.path.join(MOCK_DIR, "generic_review_sentiment_1200.json")

MIN_REVIEWS = 100
MAX_REVIEWS = 500
BATCH_SIZE = 5000


def main():
    with open(REVIEWS_JSON, encoding="utf-8") as f:
        review_pool = json.load(f)

    review_texts = [r["review"] for r in review_pool]
    print(f"Loaded {len(review_texts)} review samples from {REVIEWS_JSON}")

    with Session(engine) as db:
        product_ids = [pid for (pid,) in db.query(Product.id).all()]
        user_ids = [uid for (uid,) in db.query(User.id).all()]

    if not product_ids:
        print("ERROR: No products found. Run seed_products.py first.")
        sys.exit(1)
    if not user_ids:
        print("ERROR: No users found. Run seed_users.py first.")
        sys.exit(1)

    print(f"Found {len(product_ids)} products, {len(user_ids)} users.")
    total_products = len(product_ids)

    total_created = 0
    batch: list[dict] = []

    conn = engine.connect()
    insert_sql = text(
        "INSERT INTO reviews (id, product_id, user_id, content) "
        "VALUES (:id, :product_id, :user_id, :content)"
    )

    try:
        for idx, pid in enumerate(product_ids, start=1):
            count = random.randint(MIN_REVIEWS, MAX_REVIEWS)
            for _ in range(count):
                batch.append({
                    "id": generate_uuid(),
                    "product_id": pid,
                    "user_id": random.choice(user_ids),
                    "content": random.choice(review_texts),
                })

            if len(batch) >= BATCH_SIZE:
                conn.execute(insert_sql, batch)
                conn.commit()
                total_created += len(batch)
                batch.clear()
                print(f"  Progress: {idx}/{total_products} products, {total_created} reviews inserted...")

        if batch:
            conn.execute(insert_sql, batch)
            conn.commit()
            total_created += len(batch)
            batch.clear()
    finally:
        conn.close()

    print(f"\nDone! Created {total_created} reviews across {total_products} products.")


if __name__ == "__main__":
    main()
