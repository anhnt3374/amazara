import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.crud.store import create_store, get_store_by_email, get_store_by_id
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.db.session import get_db
from app.models.store import Store
from app.models.user import User
from app.schemas.auth import MeResponse, StoreLoginRequest
from app.schemas.store import StoreCreate
from app.schemas.user import LoginRequest, RegisterRequest, Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if not payload or payload["type"] != "user":
        raise _unauthorized("Invalid or expired token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise _unauthorized("User not found")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or payload["type"] != "user":
        return None
    return db.query(User).filter(User.id == payload["sub"]).first()


def get_current_store(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Store:
    payload = decode_access_token(credentials.credentials)
    if not payload or payload["type"] != "store":
        raise _unauthorized("Invalid or expired token")
    store = get_store_by_id(db, payload["sub"])
    if not store:
        raise _unauthorized("Store not found")
    return store


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "store"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if get_user_by_username(db, body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    user = create_user(db, body)
    return user


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password):
        raise _unauthorized("Invalid email or password")
    token = create_access_token(subject=user.id, account_type="user")
    return Token(access_token=token)


@router.post(
    "/register-store", response_model=Token, status_code=status.HTTP_201_CREATED
)
def register_store(body: StoreCreate, db: Session = Depends(get_db)):
    if get_store_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if not body.slug:
        body = body.model_copy(update={"slug": _slugify(body.name)})
    store = create_store(db, body)
    token = create_access_token(subject=store.id, account_type="store")
    return Token(access_token=token)


@router.post("/login-store", response_model=Token)
def login_store(body: StoreLoginRequest, db: Session = Depends(get_db)):
    store = get_store_by_email(db, body.email)
    if not store or not verify_password(body.password, store.password_hash):
        raise _unauthorized("Invalid email or password")
    token = create_access_token(subject=store.id, account_type="store")
    return Token(access_token=token)


@router.post("/logout")
def logout():
    # JWT is stateless — client is responsible for discarding the token
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse)
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise _unauthorized("Invalid or expired token")

    if payload["type"] == "store":
        store = get_store_by_id(db, payload["sub"])
        if not store:
            raise _unauthorized("Store not found")
        return MeResponse(
            type="store",
            id=store.id,
            email=store.email,
            display_name=store.name,
            avatar=store.avatar_url,
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise _unauthorized("User not found")
    return MeResponse(
        type="user",
        id=user.id,
        email=user.email,
        display_name=user.fullname or user.username,
        fullname=user.fullname,
        username=user.username,
        avatar=user.avatar,
    )
