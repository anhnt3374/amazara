from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str


class BrandUpdate(BaseModel):
    name: str | None = None


class BrandOut(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}
