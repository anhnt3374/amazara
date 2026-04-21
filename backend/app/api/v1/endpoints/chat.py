from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_store, get_current_user
from app.crud.conversation import (
    get_conversation_by_id,
    get_or_create_user_store,
    get_or_create_user_system,
    is_participant,
    list_by_store,
    list_by_user,
    mark_read,
    touch_last_message,
    unread_count,
)
from app.crud.message import create_message, last_message
from app.db.session import get_db
from app.models.conversation import Conversation, ConversationType
from app.models.message import SenderType
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import (
    ConversationOut,
    MessageOut,
    PartnerInfo,
    SendMessageRequest,
)
from app.services.chat.connection_manager import get_connection_manager
from app.services.chat.system_reply_service import maybe_send_system_reply

router = APIRouter(prefix="/chats", tags=["chats"])


def _system_partner() -> PartnerInfo:
    return PartnerInfo(id=None, display_name="Amaraza Assistant", avatar=None)


def _store_partner(store: Store | None) -> PartnerInfo:
    if store is None:
        return PartnerInfo(id=None, display_name="Unknown store", avatar=None)
    return PartnerInfo(id=store.id, display_name=store.name, avatar=store.avatar_url)


def _user_partner(user: User | None) -> PartnerInfo:
    if user is None:
        return PartnerInfo(id=None, display_name="Unknown user", avatar=None)
    return PartnerInfo(
        id=user.id,
        display_name=user.fullname or user.username,
        avatar=user.avatar,
    )


def _serialize_conversation(
    db: Session,
    conv: Conversation,
    *,
    viewer: str,  # "user" | "store"
) -> ConversationOut:
    if conv.type == ConversationType.user_system:
        partner = _system_partner()
    else:
        if viewer == "user":
            store = db.query(Store).filter(Store.id == conv.store_id).first()
            partner = _store_partner(store)
        else:
            user = db.query(User).filter(User.id == conv.user_id).first()
            partner = _user_partner(user)

    last = last_message(db, conv.id)
    return ConversationOut(
        id=conv.id,
        type=conv.type,
        user_id=conv.user_id,
        store_id=conv.store_id,
        partner=partner,
        last_message=MessageOut.model_validate(last) if last else None,
        unread_count=unread_count(db, conv, as_user=(viewer == "user")),
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


async def _broadcast_message(conv: Conversation, msg: MessageOut) -> None:
    cm = get_connection_manager()
    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": msg.model_dump(mode="json"),
    }
    await cm.send_to("user", conv.user_id, payload)
    if conv.store_id is not None:
        await cm.send_to("store", conv.store_id, payload)


def _resolve_participant(
    db: Session,
    conversation_id: str,
    *,
    user_id: str | None = None,
    store_id: str | None = None,
) -> Conversation:
    conv = get_conversation_by_id(db, conversation_id)
    if not conv or not is_participant(conv, user_id=user_id, store_id=store_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conv


# ── USER-SIDE ────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ConversationOut])
def list_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convs = list_by_user(db, current_user.id)
    # Ensure the user always has a system conversation in the list.
    if not any(c.type == ConversationType.user_system for c in convs):
        get_or_create_user_system(db, current_user.id)
        convs = list_by_user(db, current_user.id)
    return [_serialize_conversation(db, c, viewer="user") for c in convs]


@router.get("/store", response_model=list[ConversationOut])
def list_store_conversations(
    db: Session = Depends(get_db),
    current_store: Store = Depends(get_current_store),
):
    convs = list_by_store(db, current_store.id)
    return [_serialize_conversation(db, c, viewer="store") for c in convs]


@router.post("/system", response_model=ConversationOut)
def open_system_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = get_or_create_user_system(db, current_user.id)
    return _serialize_conversation(db, conv, viewer="user")


@router.post("/with-store/{store_id}", response_model=ConversationOut)
def open_store_conversation(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Store not found"
        )
    conv = get_or_create_user_store(db, current_user.id, store_id)
    return _serialize_conversation(db, conv, viewer="user")


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages_as_user(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    before: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _resolve_participant(db, conversation_id, user_id=current_user.id)
    msgs = list_by_conversation(db, conv.id, limit=limit, before_id=before)
    return [MessageOut.model_validate(m) for m in msgs]


@router.get(
    "/store/{conversation_id}/messages", response_model=list[MessageOut]
)
def list_messages_as_store(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    before: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_store: Store = Depends(get_current_store),
):
    conv = _resolve_participant(db, conversation_id, store_id=current_store.id)
    msgs = list_by_conversation(db, conv.id, limit=limit, before_id=before)
    return [MessageOut.model_validate(m) for m in msgs]


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def send_message_as_user(
    conversation_id: str,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _resolve_participant(db, conversation_id, user_id=current_user.id)
    if not body.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content is required",
        )
    msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=SenderType.user,
        sender_id=current_user.id,
        content=body.content,
        ref_type=body.ref_type,
        ref_id=body.ref_id,
    )
    touch_last_message(db, conv, msg.created_at)
    out = MessageOut.model_validate(msg)
    await _broadcast_message(conv, out)

    await maybe_send_system_reply(
        db,
        conv,
        current_user,
        body.content,
        transport="rest",
        broadcaster=_broadcast_message,
    )
    return out


@router.post("/store/{conversation_id}/messages", response_model=MessageOut)
async def send_message_as_store(
    conversation_id: str,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_store: Store = Depends(get_current_store),
):
    conv = _resolve_participant(db, conversation_id, store_id=current_store.id)
    if conv.type != ConversationType.user_store:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store cannot send to this conversation type",
        )
    if not body.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content is required",
        )
    msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=SenderType.store,
        sender_id=current_store.id,
        content=body.content,
        ref_type=body.ref_type,
        ref_id=body.ref_id,
    )
    touch_last_message(db, conv, msg.created_at)
    out = MessageOut.model_validate(msg)
    await _broadcast_message(conv, out)
    return out


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read_as_user(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _resolve_participant(db, conversation_id, user_id=current_user.id)
    mark_read(
        db, conv, as_user=True, at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return None


@router.post("/store/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read_as_store(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_store: Store = Depends(get_current_store),
):
    conv = _resolve_participant(db, conversation_id, store_id=current_store.id)
    mark_read(
        db, conv, as_user=False, at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return None
