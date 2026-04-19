from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


def create_review(db: Session, user_id: str, data: ReviewCreate) -> Review:
    review = Review(
        product_id=data.product_id,
        user_id=user_id,
        rating=data.rating,
        content=data.content,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    # Eager-load user for response serialisation
    db.refresh(review, attribute_names=["user"])
    return review


def get_review_by_id(db: Session, review_id: str) -> Review | None:
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews_by_product(db: Session, product_id: str) -> list[Review]:
    return (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def get_reviews_page(
    db: Session,
    product_id: str,
    rating: int | None = None,
    page: int = 1,
    page_size: int = 5,
) -> tuple[list[Review], int]:
    query = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
    )
    if rating is not None:
        query = query.filter(Review.rating == rating)
    total = query.count()
    reviews = (
        query.order_by(Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return reviews, total


def get_review_breakdown(db: Session, product_id: str) -> dict[int, int]:
    rows = (
        db.query(Review.rating, func.count(Review.id))
        .filter(Review.product_id == product_id)
        .group_by(Review.rating)
        .all()
    )
    breakdown = {star: 0 for star in range(1, 6)}
    for rating, count in rows:
        if rating in breakdown:
            breakdown[rating] = int(count)
    return breakdown


def get_reviews_by_user(db: Session, user_id: str) -> list[Review]:
    return db.query(Review).filter(Review.user_id == user_id).all()


def get_review_aggregate(db: Session, product_id: str) -> dict:
    row = (
        db.query(func.count(Review.id), func.avg(Review.rating))
        .filter(Review.product_id == product_id)
        .one()
    )
    count = int(row[0] or 0)
    average = float(row[1]) if row[1] is not None else None
    return {"count": count, "average": average}


def update_review(db: Session, review: Review, data: ReviewUpdate) -> Review:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
