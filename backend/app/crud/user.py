from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import RegisterRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, data: RegisterRequest) -> User:
    user = User(
        email=data.email,
        username=data.username,
        password=hash_password(data.password),
        fullname=data.fullname,
        avatar=data.avatar,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
