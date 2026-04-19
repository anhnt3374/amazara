from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.product import get_product_by_id
from app.crud.review import (
    create_review,
    get_review_aggregate,
    get_review_breakdown,
    get_reviews_page,
)
from app.db.session import get_db
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewBreakdown, ReviewCreate, ReviewOut, ReviewPage

router = APIRouter(tags=["reviews"])


def _serialize(review: Review) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        product_id=review.product_id,
        user_id=review.user_id,
        user_fullname=review.user.fullname,
        rating=review.rating,
        content=review.content,
        created_at=review.created_at,
    )


@router.get("/products/{product_id}/reviews", response_model=ReviewPage)
def list_for_product(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    rating: int | None = Query(None, ge=1, le=5),
    db: Session = Depends(get_db),
):
    if not get_product_by_id(db, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    reviews, total = get_reviews_page(
        db, product_id, rating=rating, page=page, page_size=page_size
    )
    aggregate = get_review_aggregate(db, product_id)
    breakdown = get_review_breakdown(db, product_id)
    return ReviewPage(
        reviews=[_serialize(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        overall_count=aggregate["count"],
        overall_average=aggregate["average"],
        breakdown=ReviewBreakdown(
            one=breakdown[1],
            two=breakdown[2],
            three=breakdown[3],
            four=breakdown[4],
            five=breakdown[5],
        ),
    )


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create(
    body: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not get_product_by_id(db, body.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    review = create_review(db, user_id=current_user.id, data=body)
    return _serialize(review)
