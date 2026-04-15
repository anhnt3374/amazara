from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.crud.address import (
    create_address,
    delete_address,
    get_address_by_id,
    get_addresses_by_user,
    update_address,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("/", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create(
    body: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_address(db, user_id=current_user.id, data=body)


@router.get("/", response_model=list[AddressOut])
def list_mine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_addresses_by_user(db, user_id=current_user.id)


@router.get("/{address_id}", response_model=AddressOut)
def get_one(
    address_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return address


@router.put("/{address_id}", response_model=AddressOut)
def update(
    address_id: str,
    body: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return update_address(db, address, body)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    address_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    delete_address(db, address)
