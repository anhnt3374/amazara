from pydantic import BaseModel, EmailStr


class StoreCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    slug: str | None = None
    avatar_url: str | None = None
    description: str | None = None


class StoreUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    avatar_url: str | None = None
    description: str | None = None


class StoreOut(BaseModel):
    id: str
    name: str
    slug: str | None
    email: str
    avatar_url: str | None
    description: str | None

    model_config = {"from_attributes": True}
