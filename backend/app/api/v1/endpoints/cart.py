from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.cart_item import (
    add_or_increment_cart_item,
    bulk_delete_cart_items,
    delete_cart_item,
    get_cart_item_by_id,
    get_enriched_cart_items,
    update_cart_item,
)
from app.crud.product import get_product_by_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart_item import (
    BulkDeleteResponse,
    CartItemBulkDelete,
    CartItemCreate,
    CartItemOut,
    CartItemUpdate,
    CartListResponse,
    EnrichedCartItemOut,
    ProductMini,
    StoreMini,
)

router = APIRouter(prefix="/cart", tags=["cart"])


def _enrich(item) -> EnrichedCartItemOut:
    product = item.product
    store = product.store
    category_name = product.category.name if product.category else None
    return EnrichedCartItemOut(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        notes=item.notes,
        product=ProductMini(
            id=product.id,
            name=product.name,
            price=product.price,
            discount=product.discount,
            image=product.image,
            stock=product.stock,
            category_id=product.category_id,
            store_id=product.store_id,
            category_name=category_name,
        ),
        store=StoreMini(
            id=store.id,
            name=store.name,
            slug=store.slug,
            avatar_url=store.avatar_url,
        ),
    )


@router.get("/", response_model=CartListResponse)
def list_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = get_enriched_cart_items(db, user_id=current_user.id)
    enriched = [_enrich(i) for i in items]
    return CartListResponse(items=enriched, total_count=len(enriched))


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


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete(
    body: CartItemBulkDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = bulk_delete_cart_items(db, user_id=current_user.id, ids=body.ids)
    return BulkDeleteResponse(deleted=deleted)


@router.patch("/{item_id}", response_model=CartItemOut)
def update_item(
    item_id: str,
    body: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_cart_item_by_id(db, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    if body.quantity is not None and body.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantity must be at least 1",
        )
    return update_cart_item(db, item, body)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_cart_item_by_id(db, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    delete_cart_item(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
