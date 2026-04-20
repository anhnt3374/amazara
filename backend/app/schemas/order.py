from datetime import datetime

from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: int
    notes: str | None = None


class OrderCreate(BaseModel):
    place: str
    phone: str
    client_name: str
    total_amount: int
    note: str | None = None
    items: list[OrderItemCreate]
    cart_item_ids: list[str] | None = None


class OrderUpdate(BaseModel):
    note: str | None = None


class OrderItemStoreMini(BaseModel):
    id: str
    name: str
    slug: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class OrderItemOut(BaseModel):
    id: str
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    price: int
    notes: str | None
    product_image: str | None = None
    store: OrderItemStoreMini | None = None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    user_id: str
    place: str
    phone: str
    client_name: str
    total_amount: int
    status: OrderStatus
    note: str | None
    created_at: datetime | None = None
    order_items: list[OrderItemOut]

    model_config = {"from_attributes": True}
