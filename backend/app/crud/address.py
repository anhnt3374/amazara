from sqlalchemy.orm import Session

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


def create_address(db: Session, user_id: str, data: AddressCreate) -> Address:
    address = Address(
        user_id=user_id,
        place=data.place,
        phone=data.phone,
        client_name=data.client_name,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def get_address_by_id(db: Session, address_id: str) -> Address | None:
    return db.query(Address).filter(Address.id == address_id).first()


def get_addresses_by_user(db: Session, user_id: str) -> list[Address]:
    return db.query(Address).filter(Address.user_id == user_id).all()


def update_address(db: Session, address: Address, data: AddressUpdate) -> Address:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
