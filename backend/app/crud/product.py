import asyncio
import concurrent.futures
import math
import random

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.search.search_service import semantic_search


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


def _post_sort_key(sort: str):
    if sort == "newest":
        return lambda p: p.created_at, True
    if sort == "price-high-low":
        return lambda p: p.price, True
    if sort == "price-low-high":
        return lambda p: p.price, False
    if sort == "discount-rate":
        return lambda p: p.discount, True
    return None


def _resolve_filter_ids(
    db: Session,
    *,
    brand_ids: list[str] | None,
    category_ids: list[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """Resolve brand_ids → category_id list, intersecting with category_ids."""
    final_cats = category_ids
    if brand_ids:
        rows = (
            db.query(Category.id)
            .filter(Category.brand_id.in_(brand_ids))
            .all()
        )
        cat_from_brand = [r[0] for r in rows]
        final_cats = (
            list(set(final_cats) & set(cat_from_brand)) if final_cats else cat_from_brand
        )
    return final_cats, None  # brand filter applied via category_ids


def _facet_brands(db: Session, category_ids: list[str] | None):
    q = db.query(Category.brand_id).distinct()
    if category_ids:
        q = q.filter(Category.id.in_(category_ids))
    brand_ids_present = [r[0] for r in q.all() if r[0] is not None]
    if not brand_ids_present:
        return []
    return db.query(Brand).filter(Brand.id.in_(brand_ids_present)).all()


def _facet_categories(db: Session, brand_ids: list[str] | None):
    q = db.query(Category)
    if brand_ids:
        q = q.filter(Category.brand_id.in_(brand_ids))
    return q.all()


def _lexical_search(
    db: Session,
    *,
    brand_ids: list[str] | None,
    category_ids: list[str] | None,
    sort: str,
    page: int,
) -> dict:
    """No-query path: kept identical to the previous behavior."""
    base = db.query(Product)
    if category_ids:
        base = base.filter(Product.category_id.in_(category_ids))
    if brand_ids:
        base = base.join(Category, Product.category_id == Category.id).filter(
            Category.brand_id.in_(brand_ids)
        )

    total = min(base.count(), MAX_TOTAL)

    if sort == "newest":
        base = base.order_by(Product.created_at.desc())
    elif sort == "price-high-low":
        base = base.order_by(Product.price.desc())
    elif sort == "price-low-high":
        base = base.order_by(Product.price.asc())
    elif sort == "discount-rate":
        base = base.order_by(Product.discount.desc())

    max_page = max(math.ceil(total / PAGE_SIZE), 1)
    page = min(page, max_page)
    products = base.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

    available_brands = _facet_brands(db, category_ids)
    available_categories = _facet_categories(db, brand_ids)

    return {
        "products": products,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "available_brands": available_brands,
        "available_categories": available_categories,
    }


def search_products(
    db: Session,
    search: str | None = None,
    brand_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    sort: str = "best-sellers",
    page: int = 1,
) -> dict:
    if not search or not search.strip():
        return _lexical_search(
            db,
            brand_ids=brand_ids,
            category_ids=category_ids,
            sort=sort,
            page=page,
        )

    resolved_cats, _ = _resolve_filter_ids(
        db, brand_ids=brand_ids, category_ids=category_ids
    )

    coro = semantic_search(
        search,
        brand_ids=None,            # already merged into resolved_cats
        category_ids=resolved_cats,
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Called from within an async context (e.g. chat service).
        # Run the coroutine in a fresh thread with its own event loop.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            ranked = pool.submit(asyncio.run, coro).result()
    else:
        ranked = asyncio.run(coro)

    if not ranked:
        return {
            "products": [],
            "total": 0,
            "page": 1,
            "page_size": PAGE_SIZE,
            "available_brands": [],
            "available_categories": [],
        }

    # Hydrate Product rows in ranked order.
    ranked_ids = [pid for pid, _ in ranked]
    rows = db.query(Product).filter(Product.id.in_(ranked_ids)).all()
    by_id = {p.id: p for p in rows}
    ordered: list[Product] = [by_id[pid] for pid in ranked_ids if pid in by_id]

    # Post-rank sort if user requested anything other than relevance.
    sort_spec = _post_sort_key(sort)
    if sort_spec is not None:
        key, reverse = sort_spec
        ordered = sorted(ordered, key=key, reverse=reverse)

    total = len(ordered)
    max_page = max(math.ceil(total / PAGE_SIZE), 1)
    page = min(page, max_page)
    page_products = ordered[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    # Facets from the candidate set.
    cand_cats = {p.category_id for p in ordered if p.category_id}
    cand_brands_q = (
        db.query(Category.brand_id)
        .filter(Category.id.in_(cand_cats))
        .distinct()
    )
    cand_brand_ids = [r[0] for r in cand_brands_q.all() if r[0] is not None]
    available_brands = (
        db.query(Brand).filter(Brand.id.in_(cand_brand_ids)).all()
        if cand_brand_ids
        else []
    )
    available_categories = (
        db.query(Category).filter(Category.id.in_(cand_cats)).all()
        if cand_cats
        else []
    )

    return {
        "products": page_products,
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
