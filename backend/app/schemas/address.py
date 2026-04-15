from pydantic import BaseModel


class AddressCreate(BaseModel):
    place: str
    phone: str
    client_name: str


class AddressUpdate(BaseModel):
    place: str | None = None
    phone: str | None = None
    client_name: str | None = None


class AddressOut(BaseModel):
    id: str
    user_id: str
    place: str
    phone: str
    client_name: str

    model_config = {"from_attributes": True}
