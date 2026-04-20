from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.v1.endpoints.auth import get_current_user_optional
from app.crud.favorite import (
    get_user_favorite_product_ids,
    is_favorited as is_product_favorited,
)
from app.crud.product import get_similar_products, search_products
from app.crud.review import get_review_aggregate
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductDetailOut,
    ProductOut,
    ProductSearchResponse,
    SimilarProductsResponse,
)


def _to_product_out(product: Product, favorited_ids: set[str]) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        discount=product.discount,
        image=product.image,
        stock=product.stock,
        category_id=product.category_id,
        store_id=product.store_id,
        is_favorited=product.id in favorited_ids,
    )

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search", response_model=ProductSearchResponse)
def search(
    search: str | None = Query(None),
    brand_ids: list[str] | None = Query(None),
    category_ids: list[str] | None = Query(None),
    page: int = Query(1, ge=1, le=25),
    sort: str = Query("best-sellers"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    result = search_products(
        db,
        search=search,
        brand_ids=brand_ids,
        category_ids=category_ids,
        sort=sort,
        page=page,
    )
    favorited_ids = (
        get_user_favorite_product_ids(db, current_user.id) if current_user else set()
    )
    result["products"] = [_to_product_out(p, favorited_ids) for p in result["products"]]
    return result


@router.get("/{product_id}/similar", response_model=SimilarProductsResponse)
def similar(
    product_id: str,
    page: int = Query(1, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if not db.query(Product.id).filter(Product.id == product_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    result = get_similar_products(db, product_id=product_id, page=page)
    favorited_ids = (
        get_user_favorite_product_ids(db, current_user.id) if current_user else set()
    )
    result["products"] = [_to_product_out(p, favorited_ids) for p in result["products"]]
    return result


@router.get("/{product_id}", response_model=ProductDetailOut)
def get_one(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.category).joinedload(Category.brand))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    aggregate = get_review_aggregate(db, product_id)
    favorited = (
        is_product_favorited(db, user_id=current_user.id, product_id=product_id)
        if current_user
        else False
    )

    category_name = product.category.name if product.category else None
    brand_name = (
        product.category.brand.name
        if product.category and product.category.brand
        else None
    )

    return ProductDetailOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        discount=product.discount,
        image=product.image,
        stock=product.stock,
        category_id=product.category_id,
        store_id=product.store_id,
        is_favorited=favorited,
        category_name=category_name,
        brand_name=brand_name,
        review_count=aggregate["count"],
        average_rating=aggregate["average"],
    )
