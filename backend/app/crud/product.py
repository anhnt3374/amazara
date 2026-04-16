from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        discount=data.discount,
        image=data.image,
        low_tier=data.low_tier,
        category_id=data.category_id,
        store_id=data.store_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product_by_id(db: Session, product_id: str) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session) -> list[Product]:
    return db.query(Product).all()


def get_products_by_store(db: Session, store_id: str) -> list[Product]:
    return db.query(Product).filter(Product.store_id == store_id).all()


def get_products_by_category(db: Session, category_id: str) -> list[Product]:
    return db.query(Product).filter(Product.category_id == category_id).all()


def update_product(db: Session, product: Product, data: ProductUpdate) -> Product:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
