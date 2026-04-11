---
feature: database
doc_type: schema
tags: [tables, foreign-keys, relationships, uuid]
---

# Database — Schema

## Relationship Tree

```
users
├── orders          (FK: user_id → users.id)
├── cart_items      (FK: user_id → users.id)
├── addresses       (FK: user_id → users.id)
└── reviews         (FK: user_id → users.id)

brands
└── categories      (FK: brand_id → brands.id)
    └── products    (FK: category_id → categories.id)
        ├── order_items  (FK: product_id → products.id)
        ├── cart_items   (FK: product_id → products.id)
        └── reviews      (FK: product_id → products.id)
```

## All 9 Tables

| Table | Primary FK(s) |
|---|---|
| `users` | — |
| `brands` | — |
| `categories` | `brand_id → brands.id` |
| `products` | `category_id → categories.id` |
| `orders` | `user_id → users.id` |
| `order_items` | `order_id → orders.id`, `product_id → products.id` |
| `cart_items` | `user_id → users.id`, `product_id → products.id` |
| `addresses` | `user_id → users.id` |
| `reviews` | `user_id → users.id`, `product_id → products.id` |

## Model Files

Each table has a corresponding model file in `backend/app/models/`:

```
backend/app/models/
├── user.py
├── brand.py
├── category.py
├── product.py
├── order.py
├── order_item.py
├── cart_item.py
├── address.py
└── review.py
```

All models inherit `Base` + `UUIDMixin` (string UUID PK, auto-generated).

## Adding a Table

1. Create `backend/app/models/<name>.py` (inherit `Base`, `UUIDMixin`)
2. Add import in `backend/app/db/base.py`
3. Run migrations:
   ```bash
   make makemigrations msg="add_<name>_table"
   make migrate
   ```

See `docs/features/backend/flows.md` for the full new-endpoint checklist.
