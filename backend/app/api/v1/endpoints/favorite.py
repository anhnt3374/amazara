from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.favorite import (
    add_favorite,
    list_favorite_products,
    remove_favorite,
)
from app.crud.product import get_product_by_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteOut
from app.schemas.product import ProductOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def create(
    body: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not get_product_by_id(db, body.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return add_favorite(db, user_id=current_user.id, product_id=body.product_id)


@router.get("/", response_model=list[ProductOut])
def list_mine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    products = list_favorite_products(db, user_id=current_user.id)
    return [
        ProductOut(
            id=p.id,
            name=p.name,
            description=p.description,
            price=p.price,
            discount=p.discount,
            image=p.image,
            stock=p.stock,
            category_id=p.category_id,
            store_id=p.store_id,
            is_favorited=True,
        )
        for p in products
    ]


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = remove_favorite(db, user_id=current_user.id, product_id=product_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )
