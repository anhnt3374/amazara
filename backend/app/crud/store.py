from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate


def create_store(db: Session, data: StoreCreate) -> Store:
    store = Store(
        name=data.name,
        slug=data.slug,
        email=data.email,
        password_hash=hash_password(data.password),
        avatar_url=data.avatar_url,
        description=data.description,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def get_store_by_id(db: Session, store_id: str) -> Store | None:
    return db.query(Store).filter(Store.id == store_id).first()


def get_store_by_email(db: Session, email: str) -> Store | None:
    return db.query(Store).filter(Store.email == email).first()


def get_stores(db: Session) -> list[Store]:
    return db.query(Store).all()


def update_store(db: Session, store: Store, data: StoreUpdate) -> Store:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    return store


def delete_store(db: Session, store: Store) -> None:
    db.delete(store)
    db.commit()
