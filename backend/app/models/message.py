import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class SenderType(str, enum.Enum):
    user = "user"
    store = "store"
    bot = "bot"
    system = "system"


class MessageRefType(str, enum.Enum):
    product = "product"
    order = "order"
    order_event = "order_event"


class Message(Base, UUIDMixin):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_type: Mapped[SenderType] = mapped_column(
        SAEnum(
            SenderType,
            name="sendertype",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    sender_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ref_type: Mapped[MessageRefType | None] = mapped_column(
        SAEnum(
            MessageRefType,
            name="messagereftype",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    ref_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ref_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
