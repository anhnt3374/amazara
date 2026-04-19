from datetime import datetime

from pydantic import BaseModel


class FavoriteCreate(BaseModel):
    product_id: str


class FavoriteOut(BaseModel):
    id: str
    product_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
