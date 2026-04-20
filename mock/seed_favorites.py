"""Seed 0–40 random favorite products per user.

Requires users and products to be seeded first.
Each user's favorites are chosen by sampling distinct products, which
naturally satisfies the (user_id, product_id) uniqueness constraint.
Streams every insert to favorites.csv as well.
"""

import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401
from app.db.session import engine
from app.models.base import generate_uuid
from app.models.product import Product
from app.models.user import User

from sqlalchemy import text
from sqlalchemy.orm import Session

MOCK_DIR = os.path.dirname(__file__)
FAVORITES_CSV = os.path.join(MOCK_DIR, "favorites.csv")

MIN_FAVORITES = 0
MAX_FAVORITES = 40
BATCH_SIZE = 5000


def main():
    with Session(engine) as db:
        user_ids = [uid for (uid,) in db.query(User.id).all()]
        product_ids = [pid for (pid,) in db.query(Product.id).all()]

    if not user_ids:
        print("ERROR: No users found. Run seed_users.py first.")
        sys.exit(1)
    if not product_ids:
        print("ERROR: No products found. Run seed_products.py first.")
        sys.exit(1)

    print(f"Found {len(user_ids)} users, {len(product_ids)} products.")

    total_created = 0
    batch: list[dict] = []

    conn = engine.connect()
    insert_sql = text(
        "INSERT INTO favorites (id, user_id, product_id) "
        "VALUES (:id, :user_id, :product_id)"
    )

    csv_file = open(FAVORITES_CSV, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(
        csv_file,
        fieldnames=["id", "user_id", "product_id"],
    )
    writer.writeheader()

    try:
        for idx, uid in enumerate(user_ids, start=1):
            count = random.randint(MIN_FAVORITES, MAX_FAVORITES)
            if count == 0:
                continue

            chosen = random.sample(product_ids, min(count, len(product_ids)))
            for pid in chosen:
                row = {
                    "id": generate_uuid(),
                    "user_id": uid,
                    "product_id": pid,
                }
                batch.append(row)
                writer.writerow(row)

            if len(batch) >= BATCH_SIZE:
                conn.execute(insert_sql, batch)
                conn.commit()
                total_created += len(batch)
                batch.clear()
                csv_file.flush()
                print(f"  Progress: {idx}/{len(user_ids)} users, {total_created} favorites...")

        if batch:
            conn.execute(insert_sql, batch)
            conn.commit()
            total_created += len(batch)
            batch.clear()
    finally:
        csv_file.close()
        conn.close()

    print(f"\nDone! Created {total_created} favorites across {len(user_ids)} users.")
    print(f"Favorites saved to: {FAVORITES_CSV}")


if __name__ == "__main__":
    main()
