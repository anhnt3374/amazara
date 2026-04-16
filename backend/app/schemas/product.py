from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: int
    store_id: str
    description: str | None = None
    discount: int = 0
    image: str | None = None
    low_tier: int = 0
    category_id: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    discount: int | None = None
    image: str | None = None
    low_tier: int | None = None
    category_id: str | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    description: str | None
    price: int
    discount: int
    image: str | None
    low_tier: int
    category_id: str | None
    store_id: str

    model_config = {"from_attributes": True}
