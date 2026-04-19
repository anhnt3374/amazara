from sqlalchemy.orm import Session, joinedload

from app.models.cart_item import CartItem
from app.models.product import Product
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


def add_or_increment_cart_item(
    db: Session, user_id: str, data: CartItemCreate
) -> CartItem:
    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == user_id, CartItem.product_id == data.product_id)
        .first()
    )
    if existing:
        existing.quantity = existing.quantity + data.quantity
        if data.notes is not None:
            existing.notes = data.notes
        db.commit()
        db.refresh(existing)
        return existing
    return create_cart_item(db, user_id=user_id, data=data)


def get_cart_item_by_id(db: Session, cart_item_id: str) -> CartItem | None:
    return db.query(CartItem).filter(CartItem.id == cart_item_id).first()


def get_cart_items_by_user(db: Session, user_id: str) -> list[CartItem]:
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


def get_enriched_cart_items(db: Session, user_id: str) -> list[CartItem]:
    return (
        db.query(CartItem)
        .options(
            joinedload(CartItem.product).joinedload(Product.store),
            joinedload(CartItem.product).joinedload(Product.category),
        )
        .filter(CartItem.user_id == user_id)
        .order_by(CartItem.created_at.desc())
        .all()
    )


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


def bulk_delete_cart_items(db: Session, user_id: str, ids: list[str]) -> int:
    if not ids:
        return 0
    deleted = (
        db.query(CartItem)
        .filter(CartItem.user_id == user_id, CartItem.id.in_(ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted or 0)
