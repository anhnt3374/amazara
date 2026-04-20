from typing import Literal

from pydantic import BaseModel, EmailStr


class StoreLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeResponse(BaseModel):
    type: Literal["user", "store"]
    id: str
    email: str
    display_name: str
    fullname: str | None = None
    username: str | None = None
    avatar: str | None = None
