from sqlalchemy import Boolean, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AssistantOrderDraft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assistant_order_drafts"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    order_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
