from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.message import Message, MessageRefType, SenderType


def create_message(
    db: Session,
    *,
    conversation_id: str,
    sender_type: SenderType,
    sender_id: str | None,
    content: str,
    ref_type: MessageRefType | None = None,
    ref_id: str | None = None,
    ref_payload: dict[str, Any] | None = None,
    assistant_payload: dict[str, Any] | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        sender_type=sender_type,
        sender_id=sender_id,
        content=content,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_payload=ref_payload,
        assistant_payload=assistant_payload,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_by_conversation(
    db: Session,
    conversation_id: str,
    *,
    limit: int = 50,
    before_id: str | None = None,
) -> list[Message]:
    q = db.query(Message).filter(Message.conversation_id == conversation_id)
    if before_id is not None:
        anchor = db.query(Message).filter(Message.id == before_id).first()
        if anchor is not None:
            q = q.filter(Message.created_at < anchor.created_at)
    return (
        q.order_by(Message.created_at.desc())
        .limit(limit)
        .all()[::-1]
    )


def last_message(db: Session, conversation_id: str) -> Message | None:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .first()
    )
