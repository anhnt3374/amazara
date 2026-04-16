from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, data: CategoryCreate) -> Category:
    category = Category(name=data.name, brand_id=data.brand_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_category_by_id(db: Session, category_id: str) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def get_categories(db: Session) -> list[Category]:
    return db.query(Category).all()


def get_categories_by_brand(db: Session, brand_id: str) -> list[Category]:
    return db.query(Category).filter(Category.brand_id == brand_id).all()


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()
