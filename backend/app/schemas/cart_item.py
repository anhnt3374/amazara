from pydantic import BaseModel


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1
    notes: str | None = None


class CartItemUpdate(BaseModel):
    quantity: int | None = None
    notes: str | None = None


class CartItemOut(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int
    notes: str | None

    model_config = {"from_attributes": True}
