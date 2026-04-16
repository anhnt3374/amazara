from pydantic import BaseModel


class ReviewCreate(BaseModel):
    product_id: str
    content: str


class ReviewUpdate(BaseModel):
    content: str | None = None


class ReviewOut(BaseModel):
    id: str
    product_id: str
    user_id: str
    content: str

    model_config = {"from_attributes": True}
