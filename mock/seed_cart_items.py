"""Seed 0–99 random cart items per user.

Requires users and products to be seeded first.
"""

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
        "INSERT INTO cart_items (id, user_id, product_id, quantity, notes) "
        "VALUES (:id, :user_id, :product_id, :quantity, :notes)"
    )

    try:
        for idx, uid in enumerate(user_ids, start=1):
            count = random.randint(0, 99)
            if count == 0:
                continue

            chosen = random.sample(product_ids, min(count, len(product_ids)))
            for pid in chosen:
                batch.append({
                    "id": generate_uuid(),
                    "user_id": uid,
                    "product_id": pid,
                    "quantity": random.randint(1, 5),
                    "notes": None,
                })

            if len(batch) >= BATCH_SIZE:
                conn.execute(insert_sql, batch)
                conn.commit()
                total_created += len(batch)
                batch.clear()
                print(f"  Progress: {idx}/{len(user_ids)} users, {total_created} cart items...")

        if batch:
            conn.execute(insert_sql, batch)
            conn.commit()
            total_created += len(batch)
            batch.clear()
    finally:
        conn.close()

    print(f"\nDone! Created {total_created} cart items across {len(user_ids)} users.")


if __name__ == "__main__":
    main()
