from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Brand(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    categories: Mapped[list["Category"]] = relationship(back_populates="brand")
