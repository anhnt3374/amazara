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


class StoreMini(BaseModel):
    id: str
    name: str
    slug: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class ProductMini(BaseModel):
    id: str
    name: str
    price: int
    discount: int
    image: str | None
    stock: int
    category_id: str | None
    store_id: str
    category_name: str | None


class EnrichedCartItemOut(BaseModel):
    id: str
    product_id: str
    quantity: int
    notes: str | None
    product: ProductMini
    store: StoreMini


class CartListResponse(BaseModel):
    items: list[EnrichedCartItemOut]
    total_count: int


class CartItemBulkDelete(BaseModel):
    ids: list[str]


class BulkDeleteResponse(BaseModel):
    deleted: int
