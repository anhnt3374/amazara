from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate


def create_order(db: Session, user_id: str, data: OrderCreate) -> Order:
    order = Order(
        user_id=user_id,
        place=data.place,
        phone=data.phone,
        client_name=data.client_name,
        total_amount=data.total_amount,
        note=data.note,
        status=OrderStatus.shipping,
    )
    db.add(order)
    db.flush()

    for item in data.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            price=item.price,
            notes=item.notes,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: str) -> Order | None:
    return (
        db.query(Order)
        .options(
            joinedload(Order.order_items)
            .joinedload(OrderItem.product)
            .joinedload(Product.store),
        )
        .filter(Order.id == order_id)
        .first()
    )


def get_orders_by_user(
    db: Session,
    user_id: str,
    status: OrderStatus | None = None,
) -> list[Order]:
    query = (
        db.query(Order)
        .options(
            joinedload(Order.order_items)
            .joinedload(OrderItem.product)
            .joinedload(Product.store),
        )
        .filter(Order.user_id == user_id)
    )
    if status is not None:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).all()


def update_order(db: Session, order: Order, data: OrderUpdate) -> Order:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order) -> Order:
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return order
