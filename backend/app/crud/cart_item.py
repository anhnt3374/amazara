from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.schemas.cart_item import CartItemCreate, CartItemUpdate


def create_cart_item(db: Session, user_id: str, data: CartItemCreate) -> CartItem:
    cart_item = CartItem(
        user_id=user_id,
        product_id=data.product_id,
        quantity=data.quantity,
        notes=data.notes,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def get_cart_item_by_id(db: Session, cart_item_id: str) -> CartItem | None:
    return db.query(CartItem).filter(CartItem.id == cart_item_id).first()


def get_cart_items_by_user(db: Session, user_id: str) -> list[CartItem]:
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


def update_cart_item(db: Session, cart_item: CartItem, data: CartItemUpdate) -> CartItem:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cart_item, key, value)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def delete_cart_item(db: Session, cart_item: CartItem) -> None:
    db.delete(cart_item)
    db.commit()
