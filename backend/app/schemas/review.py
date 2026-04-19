from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(ge=1, le=5)
    content: str


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    content: str | None = None


class ReviewOut(BaseModel):
    id: str
    product_id: str
    user_id: str
    user_fullname: str
    rating: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewBreakdown(BaseModel):
    one: int
    two: int
    three: int
    four: int
    five: int


class ReviewPage(BaseModel):
    reviews: list[ReviewOut]
    total: int
    page: int
    page_size: int
    overall_count: int
    overall_average: float | None
    breakdown: ReviewBreakdown
