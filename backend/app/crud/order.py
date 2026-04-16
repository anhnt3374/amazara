from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order import OrderCreate, OrderUpdate


def create_order(db: Session, user_id: str, data: OrderCreate) -> Order:
    order = Order(
        user_id=user_id,
        place=data.place,
        phone=data.phone,
        client_name=data.client_name,
        total_amount=data.total_amount,
        note=data.note,
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
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: str) -> Order | None:
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders_by_user(db: Session, user_id: str) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user_id).all()


def update_order(db: Session, order: Order, data: OrderUpdate) -> Order:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order
