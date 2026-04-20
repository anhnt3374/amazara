from typing import Any

from sqlalchemy.orm import Session

from app.crud.conversation import get_or_create_user_system, touch_last_message
from app.crud.message import create_message
from app.models.message import MessageRefType, SenderType
from app.models.order import Order, OrderStatus
from app.schemas.chat import MessageOut
from app.services.chat.connection_manager import get_connection_manager


async def _emit_system_message(
    db: Session,
    user_id: str,
    *,
    content: str,
    ref_type: MessageRefType | None = None,
    ref_id: str | None = None,
    ref_payload: dict[str, Any] | None = None,
) -> None:
    conv = get_or_create_user_system(db, user_id)
    msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=SenderType.system,
        sender_id=None,
        content=content,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_payload=ref_payload,
    )
    touch_last_message(db, conv, msg.created_at)

    payload = {
        "type": "message",
        "conversation_id": conv.id,
        "message": MessageOut.model_validate(msg).model_dump(mode="json"),
    }
    await get_connection_manager().send_to("user", user_id, payload)


async def notify_order_created(db: Session, user_id: str, order: Order) -> None:
    await _emit_system_message(
        db,
        user_id,
        content=f"Order #{order.id[:8]} has been placed successfully.",
        ref_type=MessageRefType.order_event,
        ref_id=order.id,
        ref_payload={
            "event": "created",
            "order_id": order.id,
            "total_amount": order.total_amount,
            "status": order.status.value,
        },
    )


async def notify_order_status_changed(
    db: Session,
    user_id: str,
    order: Order,
    *,
    old_status: OrderStatus,
    new_status: OrderStatus,
) -> None:
    await _emit_system_message(
        db,
        user_id,
        content=(
            f"Order #{order.id[:8]} status updated: "
            f"{old_status.value} → {new_status.value}."
        ),
        ref_type=MessageRefType.order_event,
        ref_id=order.id,
        ref_payload={
            "event": "status_changed",
            "order_id": order.id,
            "old_status": old_status.value,
            "new_status": new_status.value,
        },
    )


async def notify_order_cancelled(db: Session, user_id: str, order: Order) -> None:
    await _emit_system_message(
        db,
        user_id,
        content=f"Order #{order.id[:8]} has been cancelled.",
        ref_type=MessageRefType.order_event,
        ref_id=order.id,
        ref_payload={
            "event": "cancelled",
            "order_id": order.id,
        },
    )
