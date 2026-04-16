from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: int


class OrderCreate(BaseModel):
    place: str
    phone: str
    client_name: str
    total_amount: int
    note: str | None = None
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    note: str | None = None


class OrderItemOut(BaseModel):
    id: str
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    price: int

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    user_id: str
    place: str
    phone: str
    client_name: str
    total_amount: int
    note: str | None
    order_items: list[OrderItemOut]

    model_config = {"from_attributes": True}
