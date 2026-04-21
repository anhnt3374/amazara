import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud.conversation import (
    get_conversation_by_id,
    is_participant,
    mark_read,
    touch_last_message,
)
from app.crud.message import create_message
from app.db.session import get_db
from app.models.conversation import ConversationType
from app.models.message import SenderType
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import (
    MessageOut,
    WsClientRead,
    WsClientSend,
)
from app.services.chat.connection_manager import get_connection_manager
from app.services.chat.system_reply_service import maybe_send_system_reply

router = APIRouter(prefix="/ws", tags=["chat-ws"])

logger = logging.getLogger(__name__)

WS_UNAUTHORIZED = 4401


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.websocket("/chat")
async def chat_socket(
    ws: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=WS_UNAUTHORIZED)
        return
    account_type = payload.get("type")
    account_id = payload.get("sub")
    if account_type not in ("user", "store") or not account_id:
        await ws.close(code=WS_UNAUTHORIZED)
        return

    if account_type == "user":
        account = db.query(User).filter(User.id == account_id).first()
    else:
        account = db.query(Store).filter(Store.id == account_id).first()
    if account is None:
        await ws.close(code=WS_UNAUTHORIZED)
        return

    await ws.accept()
    cm = get_connection_manager()
    await cm.connect(account_type, account_id, ws)

    try:
        while True:
            raw = await ws.receive_json()
            await _handle_event(ws, db, account_type, account, raw)
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.exception("WebSocket handler crashed: %s", exc)
    finally:
        await cm.disconnect(account_type, account_id, ws)


async def _handle_event(
    ws: WebSocket,
    db: Session,
    account_type: str,
    account: User | Store,
    raw: dict,
) -> None:
    event_type = raw.get("type")
    if event_type == "send":
        try:
            event = WsClientSend.model_validate(raw)
        except ValidationError as e:
            await ws.send_json({"type": "error", "detail": str(e)})
            return
        await _handle_send(ws, db, account_type, account, event)
    elif event_type == "read":
        try:
            event = WsClientRead.model_validate(raw)
        except ValidationError as e:
            await ws.send_json({"type": "error", "detail": str(e)})
            return
        await _handle_read(ws, db, account_type, account, event)
    else:
        await ws.send_json({"type": "error", "detail": "Unknown event type"})


async def _broadcast(conv, msg_out: MessageOut) -> None:
    cm = get_connection_manager()
    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": msg_out.model_dump(mode="json"),
    }
    await cm.send_to("user", conv.user_id, payload)
    if conv.store_id is not None:
        await cm.send_to("store", conv.store_id, payload)


async def _handle_send(
    ws: WebSocket,
    db: Session,
    account_type: str,
    account: User | Store,
    event: WsClientSend,
) -> None:
    conv = get_conversation_by_id(db, event.conversation_id)
    if not conv:
        await ws.send_json({"type": "error", "detail": "Conversation not found"})
        return

    is_user = account_type == "user"
    if not is_participant(
        conv,
        user_id=account.id if is_user else None,
        store_id=account.id if not is_user else None,
    ):
        await ws.send_json({"type": "error", "detail": "Not a participant"})
        return

    if not is_user and conv.type != ConversationType.user_store:
        await ws.send_json(
            {"type": "error", "detail": "Store cannot send to this conversation"}
        )
        return

    content = (event.content or "").strip()
    if not content:
        await ws.send_json({"type": "error", "detail": "Empty message"})
        return

    sender_type = SenderType.user if is_user else SenderType.store
    msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=sender_type,
        sender_id=account.id,
        content=event.content,
        ref_type=event.ref_type,
        ref_id=event.ref_id,
    )
    touch_last_message(db, conv, msg.created_at)
    await _broadcast(conv, MessageOut.model_validate(msg))

    if is_user:
        await maybe_send_system_reply(
            db,
            conv,
            account,
            event.content,
            transport="ws",
            broadcaster=_broadcast,
        )


async def _handle_read(
    ws: WebSocket,
    db: Session,
    account_type: str,
    account: User | Store,
    event: WsClientRead,
) -> None:
    conv = get_conversation_by_id(db, event.conversation_id)
    if not conv:
        return
    is_user = account_type == "user"
    if not is_participant(
        conv,
        user_id=account.id if is_user else None,
        store_id=account.id if not is_user else None,
    ):
        return
    mark_read(db, conv, as_user=is_user, at=_now())
