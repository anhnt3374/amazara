---
feature: orders
doc_type: flows
tags: [orders, checkout, flows, cart-to-order]
---

# Orders — Flows

## Cart → Checkout → Order

1. On `/cart`, the user selects items and clicks **Buy Now**.
2. `Cart.buy()` calls `navigate('/checkout', { state: { selectedItemIds } })`.
3. `Checkout.tsx` loads `listCart(token)` + `listAddresses(token)` in parallel, filters the cart down to `selectedItemIds`, and picks `addresses[0]` as the default.
4. The user clicks **Place Order**. `createOrder` POSTs `OrderCreate` with `cart_item_ids` equal to the checkout set.
5. Backend `create_order` inserts the `Order` (status `shipping`) + one `OrderItem` per payload item (copying `product_name`, `price`, `quantity`, `notes`), then calls `bulk_delete_cart_items` for the passed `cart_item_ids`.
6. The response is re-fetched via `get_order_by_id` so enrichment (store/product image) is populated.
7. Frontend navigates to `/orders`.

## Order list

- `/orders?tab=<status>` controls which `GET /orders/?status=<status>` is issued. `tab=all` (or no tab) sends the unfiltered list request.
- The search box is client-side: filters by order id, product name, or store name on the already-fetched list.
- **Buy Again** iterates the `order_items` and `addToCart` each one, then navigates to `/cart`. Notes are re-applied as the cart-item notes.
- **Contact Seller** and the shop-header "Chat / View Shop" buttons are rendered inert until a chat integration exists.

## Disabled affordances (by design)

The design includes "Change" buttons for address, shipping method, and payment method. All three are rendered with `aria-disabled`, `tabIndex={-1}`, muted color, and no click handler — consistent with the decision to ship COD-only without shipping-method or address-picker UIs yet. The "Awaiting Payment" tab is simply not rendered, since there is no payment state.

## Fixed shipping fee

`SHIPPING_FEE_VND = 63800` in `Checkout.tsx` is added to the subtotal before POSTing. Change this constant if the shipping policy changes; no backend field is involved.

## When to add a new status value

1. Append to `OrderStatus` (backend model + frontend type).
2. Add an Alembic migration that extends the MySQL enum.
3. Add a row to the `TABS` array in `Orders.tsx` and a label to `STATUS_LABEL`.
4. Add an endpoint or background job that can actually transition orders into the new state.
