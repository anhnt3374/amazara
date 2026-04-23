from typing import Any

from sqlalchemy.orm import Session

from app.crud.address import get_addresses_by_user
from app.crud.assistant_order_draft import create_draft, get_draft, mark_used
from app.crud.order import create_order, get_order_by_id
from app.crud.product import PAGE_SIZE, get_product_by_id, search_products
from app.crud.review import get_review_aggregate
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.chat.assistant_types import AssistantExecutionResult

SHIPPING_FEE_VND = 63800


def _effective_price(price: int, discount: int) -> int:
    return price - (price * discount // 100)


def execute_search(db: Session, query: str) -> AssistantExecutionResult:
    result = search_products(db, search=query, page=1)
    items: list[dict[str, Any]] = []
    for product in result["products"]:
        items.append(
            {
                "product_id": product.id,
                "name": product.name,
                "image": product.image.split("|")[0].strip() if product.image else None,
                "price": product.price,
                "discount": product.discount,
                "final_price": _effective_price(product.price, product.discount),
                "stock": product.stock,
            }
        )
    count = len(items)
    text = f"I found {count} product{'s' if count != 1 else ''} for '{query}'."
    return AssistantExecutionResult(
        text=text,
        assistant_payload={
            "type": "product_carousel",
            "query": query,
            "page": 1,
            "page_size": PAGE_SIZE,
            "total": result["total"],
            "items": items,
        },
    )


def execute_prepare_order(
    db: Session,
    *,
    conversation_id: str,
    user: User,
    product_id: str,
    quantity: int,
) -> AssistantExecutionResult:
    product = get_product_by_id(db, product_id)
    if not product:
        return AssistantExecutionResult(text="I could not find that product code.")

    if quantity < 1:
        quantity = 1
    if product.stock < quantity:
        return AssistantExecutionResult(
            text=f"Only {product.stock} item(s) are available for this product."
        )

    addresses = get_addresses_by_user(db, user.id)
    if not addresses:
        return AssistantExecutionResult(
            text="Please add a saved address before placing an order from chat."
        )
    address = addresses[0]
    unit_price = _effective_price(product.price, product.discount)
    total_amount = unit_price * quantity + SHIPPING_FEE_VND
    order_payload = OrderCreate(
        place=address.place,
        phone=address.phone,
        client_name=address.client_name,
        total_amount=total_amount,
        note=None,
        items=[
            OrderItemCreate(
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                price=unit_price,
                notes=None,
            )
        ],
        cart_item_ids=None,
    )
    draft = create_draft(
        db,
        user_id=user.id,
        conversation_id=conversation_id,
        order_payload=order_payload.model_dump(mode="json"),
    )
    return AssistantExecutionResult(
        text="Please confirm this order and I will place it.",
        assistant_payload={
            "type": "order_confirmation",
            "quantity": quantity,
            "shipping_fee": SHIPPING_FEE_VND,
            "total_amount": total_amount,
            "address": {
                "place": address.place,
                "phone": address.phone,
                "client_name": address.client_name,
            },
            "product": {
                "product_id": product.id,
                "name": product.name,
                "image": product.image.split("|")[0].strip() if product.image else None,
                "price": product.price,
                "discount": product.discount,
                "final_price": unit_price,
            },
            "action": {
                "action_id": "confirm_order",
                "draft_id": draft.id,
                "label": "Confirm order",
            },
        },
    )


def execute_view_product(
    db: Session,
    *,
    product_id: str,
) -> AssistantExecutionResult:
    product = get_product_by_id(db, product_id)
    if not product:
        return AssistantExecutionResult(text="I could not find that product code.")

    category = product.category
    brand = category.brand if category else None
    aggregate = get_review_aggregate(db, product.id)
    final_price = _effective_price(product.price, product.discount)
    image = product.image.split("|")[0].strip() if product.image else None
    description = (product.description or "").strip() or "No description available."
    return AssistantExecutionResult(
        text=f"Here is the product information for {product.name}.",
        assistant_payload={
            "type": "product_info",
            "product": {
                "product_id": product.id,
                "name": product.name,
                "image": image,
                "price": product.price,
                "discount": product.discount,
                "final_price": final_price,
                "stock": product.stock,
                "brand_name": brand.name if brand else None,
                "category_name": category.name if category else None,
                "average_rating": aggregate["average"],
                "review_count": aggregate["count"],
                "description": description,
            },
        },
    )


def execute_confirm_order(
    db: Session,
    *,
    conversation_id: str,
    user: User,
    draft_id: str,
) -> AssistantExecutionResult:
    draft = get_draft(
        db,
        draft_id,
        user_id=user.id,
        conversation_id=conversation_id,
    )
    if not draft or draft.used:
        return AssistantExecutionResult(
            text="This order confirmation is no longer available."
        )

    order_payload = OrderCreate.model_validate(draft.order_payload)
    order = create_order(db, user_id=user.id, data=order_payload)
    order = get_order_by_id(db, order.id)
    mark_used(db, draft)
    item = order.order_items[0]
    return AssistantExecutionResult(
        text=f"Order #{order.id[:8]} has been placed successfully.",
        assistant_payload={
            "type": "order_result",
            "order": {
                "order_id": order.id,
                "status": order.status.value,
                "total_amount": order.total_amount,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
            },
        },
    )
