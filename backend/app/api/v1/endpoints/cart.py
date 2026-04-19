from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.cart_item import add_or_increment_cart_item
from app.crud.product import get_product_by_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart_item import CartItemCreate, CartItemOut

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    body: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantity must be at least 1",
        )
    if not get_product_by_id(db, body.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return add_or_increment_cart_item(db, user_id=current_user.id, data=body)
