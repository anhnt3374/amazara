from pydantic import BaseModel

from app.schemas.brand import BrandOut
from app.schemas.category import CategoryOut


class ProductCreate(BaseModel):
    name: str
    price: int
    store_id: str
    description: str | None = None
    discount: int = 0
    image: str | None = None
    stock: int = 100
    category_id: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    discount: int | None = None
    image: str | None = None
    stock: int | None = None
    category_id: str | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    description: str | None
    price: int
    discount: int
    image: str | None
    stock: int
    category_id: str | None
    store_id: str
    is_favorited: bool = False

    model_config = {"from_attributes": True}


class ProductDetailOut(ProductOut):
    category_name: str | None
    brand_name: str | None
    review_count: int
    average_rating: float | None


class ProductSearchResponse(BaseModel):
    products: list[ProductOut]
    total: int
    page: int
    page_size: int
    available_brands: list[BrandOut]
    available_categories: list[CategoryOut]


class SimilarProductsResponse(BaseModel):
    products: list[ProductOut]
    total: int
    page: int
    page_size: int
