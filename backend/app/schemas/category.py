from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    brand_id: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    brand_id: str | None = None


class CategoryOut(BaseModel):
    id: str
    name: str
    brand_id: str | None

    model_config = {"from_attributes": True}
