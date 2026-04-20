---
feature: orders
doc_type: api
tags: [orders, api, endpoints]
---

# Orders — API

All endpoints require a bearer token (`get_current_user` dependency). A 404 is returned whenever a requested order belongs to a different user.

## `POST /api/v1/orders/`

Create an order from a checkout payload. Any `cart_item_ids` passed in are deleted from the user's cart after the order is persisted.

**Request body** (`OrderCreate`):
```json
{
  "place": "123 Test St",
  "phone": "+84 900 000 000",
  "client_name": "Test User",
  "total_amount": 142800,
  "note": "Leave at the door",
  "items": [
    {
      "product_id": "uuid",
      "product_name": "Snapshot of product name",
      "quantity": 2,
      "price": 79000,
      "notes": "Color: white / 50cm"
    }
  ],
  "cart_item_ids": ["cart-item-uuid-1", "cart-item-uuid-2"]
}
```

- `total_amount` is **client-computed**; the server trusts the frontend.
- `items` must be non-empty (422 otherwise).
- `cart_item_ids` is optional.

**Response** (`OrderOut`, 201): includes `status="shipping"` and enriched `order_items` (with `product_image` + `store`).

## `GET /api/v1/orders/?status=<enum>`

List the current user's orders, newest first. `status` is optional; accepted values: `shipping`, `awaiting_delivery`, `completed`, `cancelled`, `returning`.

Each item in the response carries `product_image` and `store: {id, name, slug, avatar_url}` so the list view can render without a second round-trip.

## `GET /api/v1/orders/{order_id}`

Fetch one order. Same enrichment as the list endpoint. 404 if the order is not owned by the caller.

## `OrderStatus` enum

Backend: `app.models.order.OrderStatus` (string values).
Frontend: `OrderStatus` string union in `frontend/src/types/order.ts` — keep the two in sync.
