from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.cart_item import bulk_delete_cart_items
from app.crud.order import create_order, get_order_by_id, get_orders_by_user
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderItemOut,
    OrderItemStoreMini,
    OrderOut,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _serialize(order: Order) -> OrderOut:
    items: list[OrderItemOut] = []
    for item in order.order_items:
        product = item.product
        store = product.store if product else None
        items.append(
            OrderItemOut(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                notes=item.notes,
                product_image=product.image if product else None,
                store=(
                    OrderItemStoreMini(
                        id=store.id,
                        name=store.name,
                        slug=store.slug,
                        avatar_url=store.avatar_url,
                    )
                    if store
                    else None
                ),
            )
        )
    return OrderOut(
        id=order.id,
        user_id=order.user_id,
        place=order.place,
        phone=order.phone,
        client_name=order.client_name,
        total_amount=order.total_amount,
        status=order.status,
        note=order.note,
        created_at=order.created_at,
        order_items=items,
    )


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create(
    body: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Order must contain at least one item",
        )
    order = create_order(db, user_id=current_user.id, data=body)
    if body.cart_item_ids:
        bulk_delete_cart_items(db, user_id=current_user.id, ids=body.cart_item_ids)
    order = get_order_by_id(db, order.id)
    return _serialize(order)


@router.get("/", response_model=list[OrderOut])
def list_mine(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = get_orders_by_user(db, user_id=current_user.id, status=status_filter)
    return [_serialize(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_one(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order_by_id(db, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return _serialize(order)
