from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.v1.endpoints.auth import get_current_user_optional
from app.crud.favorite import is_favorited as is_product_favorited
from app.crud.product import search_products
from app.crud.review import get_review_aggregate
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductDetailOut, ProductSearchResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search", response_model=ProductSearchResponse)
def search(
    search: str | None = Query(None),
    brand_ids: list[str] | None = Query(None),
    category_ids: list[str] | None = Query(None),
    page: int = Query(1, ge=1, le=25),
    sort: str = Query("best-sellers"),
    db: Session = Depends(get_db),
):
    return search_products(
        db,
        search=search,
        brand_ids=brand_ids,
        category_ids=category_ids,
        sort=sort,
        page=page,
    )


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
        low_tier=product.low_tier,
        category_id=product.category_id,
        store_id=product.store_id,
        category_name=category_name,
        brand_name=brand_name,
        review_count=aggregate["count"],
        average_rating=aggregate["average"],
        is_favorited=favorited,
    )
