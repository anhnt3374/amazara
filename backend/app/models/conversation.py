import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConversationType(str, enum.Enum):
    user_store = "user_store"
    user_system = "user_system"


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user_id", "store_id", "type", name="uq_conversation_pair"),
        Index("ix_conversation_user", "user_id", "last_message_at"),
        Index("ix_conversation_store", "store_id", "last_message_at"),
    )

    type: Mapped[ConversationType] = mapped_column(
        SAEnum(
            ConversationType,
            name="conversationtype",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    store_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stores.id"), nullable=True
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_read_at_user: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_read_at_store: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
