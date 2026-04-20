from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.models.product import Product


def add_favorite(db: Session, user_id: str, product_id: str) -> Favorite:
    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.product_id == product_id)
        .first()
    )
    if existing:
        return existing
    favorite = Favorite(user_id=user_id, product_id=product_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, user_id: str, product_id: str) -> bool:
    favorite = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.product_id == product_id)
        .first()
    )
    if not favorite:
        return False
    db.delete(favorite)
    db.commit()
    return True


def get_favorites_by_user(db: Session, user_id: str) -> list[Favorite]:
    return (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .all()
    )


def is_favorited(db: Session, user_id: str, product_id: str) -> bool:
    return (
        db.query(Favorite.id)
        .filter(Favorite.user_id == user_id, Favorite.product_id == product_id)
        .first()
        is not None
    )


def get_user_favorite_product_ids(db: Session, user_id: str) -> set[str]:
    rows = db.query(Favorite.product_id).filter(Favorite.user_id == user_id).all()
    return {r[0] for r in rows}


def list_favorite_products(db: Session, user_id: str) -> list[Product]:
    return (
        db.query(Product)
        .join(Favorite, Favorite.product_id == Product.id)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
