from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationType
from app.models.message import Message


def _conversation_ordering():
    return (
        Conversation.last_message_at.is_(None),
        Conversation.last_message_at.desc(),
        Conversation.created_at.desc(),
    )


def get_conversation_by_id(db: Session, conversation_id: str) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_or_create_user_store(
    db: Session, user_id: str, store_id: str
) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.store_id == store_id,
            Conversation.type == ConversationType.user_store,
        )
        .first()
    )
    if conv:
        return conv
    conv = Conversation(
        type=ConversationType.user_store,
        user_id=user_id,
        store_id=store_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_or_create_user_system(db: Session, user_id: str) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.type == ConversationType.user_system,
            Conversation.store_id.is_(None),
        )
        .first()
    )
    if conv:
        return conv
    conv = Conversation(
        type=ConversationType.user_system,
        user_id=user_id,
        store_id=None,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_by_user(db: Session, user_id: str) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(*_conversation_ordering())
        .all()
    )


def list_by_store(db: Session, store_id: str) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.store_id == store_id)
        .order_by(*_conversation_ordering())
        .all()
    )


def touch_last_message(db: Session, conv: Conversation, at: datetime) -> None:
    conv.last_message_at = at
    db.commit()


def mark_read(
    db: Session, conv: Conversation, *, as_user: bool, at: datetime
) -> None:
    if as_user:
        conv.last_read_at_user = at
    else:
        conv.last_read_at_store = at
    db.commit()


def unread_count(db: Session, conv: Conversation, *, as_user: bool) -> int:
    read_at = conv.last_read_at_user if as_user else conv.last_read_at_store
    # Only count messages NOT sent by the viewer themselves.
    viewer_sender = "user" if as_user else "store"
    q = db.query(func.count(Message.id)).filter(
        Message.conversation_id == conv.id,
        Message.sender_type != viewer_sender,
    )
    if read_at is not None:
        q = q.filter(Message.created_at > read_at)
    return int(q.scalar() or 0)


def is_participant(
    conv: Conversation,
    *,
    user_id: str | None = None,
    store_id: str | None = None,
) -> bool:
    if user_id is not None and conv.user_id == user_id:
        return True
    if (
        store_id is not None
        and conv.type == ConversationType.user_store
        and conv.store_id == store_id
    ):
        return True
    return False
