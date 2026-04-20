---
feature: orders
doc_type: overview
tags: [orders, checkout, order-status, cart-to-order]
---

# Orders — Overview

Orders represent a placed purchase. A user selects cart items, chooses an address, and posts to `POST /api/v1/orders/`. The endpoint persists the order, copies line-item snapshots into `order_items`, and deletes the matching cart items so the cart never re-presents items that were already purchased.

## Scope

- **Placed orders only.** Orders are created in `status = shipping`. There is no payment step (COD only) and no transition workflow yet, so higher-status tabs in the UI are empty until transitions are added.
- **No variants system.** The line-item variant label is carried through `cart_item.notes` → `order_item.notes` (free-form string).
- **Fixed shipping fee.** A constant `SHIPPING_FEE_VND = 63800` is applied per checkout (not per shop); it is rolled into `total_amount` when the order is created.

## Key files

**Backend**
- `backend/app/models/order.py` — `Order` + `OrderStatus` enum (`shipping | awaiting_delivery | completed | cancelled | returning`).
- `backend/app/models/order_item.py` — `OrderItem` with `notes` for variant label.
- `backend/app/schemas/order.py` — `OrderCreate`, `OrderOut`, `OrderItemOut` (with optional `product_image` + `store` enrichment).
- `backend/app/crud/order.py` — `create_order`, `get_orders_by_user(status=...)`, `get_order_by_id`, `cancel_order`.
- `backend/app/api/v1/endpoints/order.py` — `POST /`, `GET /?status=...`, `GET /{id}`.
- `backend/alembic/versions/c1b2d3e4f5a6_add_order_status.py` — adds `orders.status` enum + `order_items.notes`.

**Frontend**
- `frontend/src/pages/Checkout.tsx` (route `/checkout`) — reads selected cart items from `navigate` state, posts the order, redirects to `/orders`.
- `frontend/src/pages/Orders.tsx` (route `/orders`) — tabbed list (`All | Shipping | Awaiting Delivery | Completed | Cancelled | Return/Refund`), client-side search, Buy Again.
- `frontend/src/services/order.ts`, `frontend/src/types/order.ts`.
- `frontend/src/utils/money.ts` — shared `formatVnd`, `priceAfterDiscount`.

## Statuses

| Value | UI label | When it's set |
|---|---|---|
| `shipping` | Shipping | Default on `create_order` |
| `awaiting_delivery` | Awaiting Delivery | _No UI yet_ |
| `completed` | Completed | _No UI yet_ |
| `cancelled` | Cancelled | `cancel_order` CRUD exists; no endpoint/UI |
| `returning` | Return/Refund | _No UI yet_ |

## Intentional gaps (not bugs)

- No "change address / shipping method / payment method" buttons — all rendered inert to match the COD-only flow.
- No "Awaiting Payment" tab — COD means there is no pending-payment state.
- "Chat", "View Shop", "Contact Seller" are placeholders until a chat feature exists.
