"""Seed 0–10 orders per user, each with 1–5 items from the same store.

Requires users, products, and addresses to be seeded first.
"""

import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401
from app.db.session import engine
from app.models.address import Address
from app.models.base import generate_uuid
from app.models.product import Product
from app.models.user import User

from sqlalchemy import text
from sqlalchemy.orm import Session

ORDER_BATCH = 2000
ITEM_BATCH = 5000


def main():
    with Session(engine) as db:
        user_ids = [uid for (uid,) in db.query(User.id).all()]

        # Build user → addresses mapping
        user_addresses: dict[str, list] = defaultdict(list)
        for addr in db.query(Address).all():
            user_addresses[addr.user_id].append(addr)

        # Build store → products mapping
        store_products: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
        for p in db.query(Product.id, Product.name, Product.price, Product.store_id).all():
            store_products[p.store_id].append((p.id, p.name, p.price))

    if not user_ids:
        print("ERROR: No users found. Run seed_users.py first.")
        sys.exit(1)
    if not store_products:
        print("ERROR: No products found. Run seed_products.py first.")
        sys.exit(1)

    store_ids = list(store_products.keys())
    print(f"Found {len(user_ids)} users, {len(store_ids)} stores.")

    total_orders = 0
    total_items = 0
    order_batch: list[dict] = []
    item_batch: list[dict] = []

    conn = engine.connect()
    order_sql = text(
        "INSERT INTO orders (id, user_id, place, phone, client_name, total_amount, note) "
        "VALUES (:id, :user_id, :place, :phone, :client_name, :total_amount, :note)"
    )
    item_sql = text(
        "INSERT INTO order_items (id, order_id, product_id, product_name, quantity, price) "
        "VALUES (:id, :order_id, :product_id, :product_name, :quantity, :price)"
    )

    def flush_orders():
        nonlocal total_orders
        if order_batch:
            conn.execute(order_sql, order_batch)
            total_orders += len(order_batch)
            order_batch.clear()

    def flush_items():
        nonlocal total_items
        if item_batch:
            conn.execute(item_sql, item_batch)
            total_items += len(item_batch)
            item_batch.clear()

    try:
        for idx, uid in enumerate(user_ids, start=1):
            order_count = random.randint(0, 10)
            if order_count == 0:
                continue

            addresses = user_addresses.get(uid)
            if not addresses:
                continue

            for _ in range(order_count):
                addr = random.choice(addresses)
                store_id = random.choice(store_ids)
                products = store_products[store_id]

                item_count = random.randint(1, min(5, len(products)))
                chosen = random.sample(products, item_count)

                order_id = generate_uuid()
                total_amount = 0

                for pid, pname, pprice in chosen:
                    qty = random.randint(1, 5)
                    total_amount += pprice * qty
                    item_batch.append({
                        "id": generate_uuid(),
                        "order_id": order_id,
                        "product_id": pid,
                        "product_name": pname[:255],
                        "quantity": qty,
                        "price": pprice,
                    })

                order_batch.append({
                    "id": order_id,
                    "user_id": uid,
                    "place": addr.place,
                    "phone": addr.phone,
                    "client_name": addr.client_name,
                    "total_amount": total_amount,
                    "note": None,
                })

            if len(order_batch) >= ORDER_BATCH:
                flush_orders()
                flush_items()
                conn.commit()
                print(f"  Progress: {idx}/{len(user_ids)} users, {total_orders} orders, {total_items} items...")

        flush_orders()
        flush_items()
        conn.commit()
    finally:
        conn.close()

    print(f"\nDone! Created {total_orders} orders with {total_items} items across {len(user_ids)} users.")


if __name__ == "__main__":
    main()
