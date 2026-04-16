from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Category(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("brands.id"), nullable=True
    )

    brand: Mapped["Brand | None"] = relationship(back_populates="categories")
    products: Mapped[list["Product"]] = relationship(back_populates="category")
