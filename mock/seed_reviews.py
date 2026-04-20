"""Seed 50–100 mock reviews per product using the sentiment sample pool.

Requires users and products to be seeded first.
Reviews are drawn from generic_review_sentiment_1200.json; the `label`
field is used as the review's `rating` (1–5). Reviewers are randomly
assigned. Each inserted review is also streamed to reviews.csv.
"""

import csv
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
REVIEWS_CSV = os.path.join(MOCK_DIR, "reviews.csv")

MIN_REVIEWS = 50
MAX_REVIEWS = 100
BATCH_SIZE = 5000


def main():
    with open(REVIEWS_JSON, encoding="utf-8") as f:
        review_pool = json.load(f)

    samples = [(int(r["label"]), r["review"]) for r in review_pool]
    print(f"Loaded {len(samples)} review samples from {REVIEWS_JSON}")

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
        "INSERT INTO reviews (id, product_id, user_id, rating, content) "
        "VALUES (:id, :product_id, :user_id, :rating, :content)"
    )

    csv_file = open(REVIEWS_CSV, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(
        csv_file,
        fieldnames=["id", "product_id", "user_id", "rating", "content"],
    )
    writer.writeheader()

    try:
        for idx, pid in enumerate(product_ids, start=1):
            count = random.randint(MIN_REVIEWS, MAX_REVIEWS)
            for _ in range(count):
                rating, content = random.choice(samples)
                row = {
                    "id": generate_uuid(),
                    "product_id": pid,
                    "user_id": random.choice(user_ids),
                    "rating": rating,
                    "content": content,
                }
                batch.append(row)
                writer.writerow(row)

            if len(batch) >= BATCH_SIZE:
                conn.execute(insert_sql, batch)
                conn.commit()
                total_created += len(batch)
                batch.clear()
                csv_file.flush()
                print(
                    f"  Progress: {idx}/{total_products} products, "
                    f"{total_created} reviews inserted..."
                )

        if batch:
            conn.execute(insert_sql, batch)
            conn.commit()
            total_created += len(batch)
            batch.clear()
    finally:
        csv_file.close()
        conn.close()

    print(f"\nDone! Created {total_created} reviews across {total_products} products.")
    print(f"Reviews saved to: {REVIEWS_CSV}")


if __name__ == "__main__":
    main()
