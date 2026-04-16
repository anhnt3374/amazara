from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandUpdate


def create_brand(db: Session, data: BrandCreate) -> Brand:
    brand = Brand(name=data.name)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def get_brand_by_id(db: Session, brand_id: str) -> Brand | None:
    return db.query(Brand).filter(Brand.id == brand_id).first()


def get_brands(db: Session) -> list[Brand]:
    return db.query(Brand).all()


def update_brand(db: Session, brand: Brand, data: BrandUpdate) -> Brand:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    db.commit()
    db.refresh(brand)
    return brand


def delete_brand(db: Session, brand: Brand) -> None:
    db.delete(brand)
    db.commit()
