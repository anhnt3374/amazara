from sqlalchemy.orm import Session

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


def create_review(db: Session, user_id: str, data: ReviewCreate) -> Review:
    review = Review(
        product_id=data.product_id,
        user_id=user_id,
        content=data.content,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_review_by_id(db: Session, review_id: str) -> Review | None:
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews_by_product(db: Session, product_id: str) -> list[Review]:
    return db.query(Review).filter(Review.product_id == product_id).all()


def get_reviews_by_user(db: Session, user_id: str) -> list[Review]:
    return db.query(Review).filter(Review.user_id == user_id).all()


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
