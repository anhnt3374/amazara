import math
import random

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        discount=data.discount,
        image=data.image,
        stock=data.stock,
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


PAGE_SIZE = 20
MAX_TOTAL = 500


def _apply_search(query, search: str | None):
    if search:
        term = search.replace("%", "\\%").replace("_", "\\_")
        query = query.filter(Product.description.ilike(f"%{term}%"))
    return query


def search_products(
    db: Session,
    search: str | None = None,
    brand_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    sort: str = "best-sellers",
    page: int = 1,
) -> dict:
    # --- base query with all filters ---
    base = db.query(Product)
    base = _apply_search(base, search)

    if category_ids:
        base = base.filter(Product.category_id.in_(category_ids))
    if brand_ids:
        base = base.join(Category, Product.category_id == Category.id).filter(
            Category.brand_id.in_(brand_ids)
        )

    # --- total (capped at 500) ---
    total = min(base.count(), MAX_TOTAL)

    # --- sort ---
    if sort == "newest":
        base = base.order_by(Product.created_at.desc())
    elif sort == "price-high-low":
        base = base.order_by(Product.price.desc())
    elif sort == "price-low-high":
        base = base.order_by(Product.price.asc())
    elif sort == "discount-rate":
        base = base.order_by(Product.discount.desc())

    # --- paginate ---
    max_page = max(math.ceil(total / PAGE_SIZE), 1)
    page = min(page, max_page)
    products = base.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

    # --- available brands (filtered by search + category_ids, NOT brand_ids) ---
    brand_base = db.query(Product.category_id).distinct()
    brand_base = _apply_search(brand_base, search)
    if category_ids:
        brand_base = brand_base.filter(Product.category_id.in_(category_ids))

    cat_ids_for_brands = [r[0] for r in brand_base.all() if r[0] is not None]
    if cat_ids_for_brands:
        brand_id_rows = (
            db.query(Category.brand_id)
            .filter(Category.id.in_(cat_ids_for_brands))
            .distinct()
            .all()
        )
        available_brand_ids = [r[0] for r in brand_id_rows if r[0] is not None]
        available_brands = (
            db.query(Brand).filter(Brand.id.in_(available_brand_ids)).all()
            if available_brand_ids
            else []
        )
    else:
        available_brands = []

    # --- available categories (filtered by search + brand_ids, NOT category_ids) ---
    cat_base = db.query(Product.category_id).distinct()
    cat_base = _apply_search(cat_base, search)
    if brand_ids:
        cat_base = cat_base.join(Category, Product.category_id == Category.id).filter(
            Category.brand_id.in_(brand_ids)
        )

    cat_id_rows = [r[0] for r in cat_base.all() if r[0] is not None]
    available_categories = (
        db.query(Category).filter(Category.id.in_(cat_id_rows)).all()
        if cat_id_rows
        else []
    )

    return {
        "products": products,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "available_brands": available_brands,
        "available_categories": available_categories,
    }


SIMILAR_PAGE_SIZE = 20
SIMILAR_MAX_TOTAL = 100


def get_similar_products(
    db: Session, product_id: str, page: int = 1
) -> dict:
    """Mock similar-products endpoint.

    Seeded by product_id so the empty/populated state and the sampled order are
    stable across refreshes for a given product.
    """
    empty_rng = random.Random(f"similar-empty::{product_id}")
    if empty_rng.random() < 0.5:
        return {
            "products": [],
            "total": 0,
            "page": 1,
            "page_size": SIMILAR_PAGE_SIZE,
        }

    candidate_ids = [
        row[0]
        for row in db.query(Product.id).filter(Product.id != product_id).all()
    ]
    if not candidate_ids:
        return {
            "products": [],
            "total": 0,
            "page": 1,
            "page_size": SIMILAR_PAGE_SIZE,
        }

    sample_rng = random.Random(f"similar-sample::{product_id}")
    sample_size = min(SIMILAR_MAX_TOTAL, len(candidate_ids))
    sampled_ids = sample_rng.sample(candidate_ids, k=sample_size)

    total = len(sampled_ids)
    max_page = max(math.ceil(total / SIMILAR_PAGE_SIZE), 1)
    page = max(1, min(page, max_page))

    page_ids = sampled_ids[(page - 1) * SIMILAR_PAGE_SIZE : page * SIMILAR_PAGE_SIZE]
    rows = db.query(Product).filter(Product.id.in_(page_ids)).all()
    by_id = {p.id: p for p in rows}
    ordered = [by_id[i] for i in page_ids if i in by_id]

    return {
        "products": ordered,
        "total": total,
        "page": page,
        "page_size": SIMILAR_PAGE_SIZE,
    }
