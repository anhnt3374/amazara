from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session

from app.crud.conversation import touch_last_message
from app.crud.message import create_message, list_by_conversation
from app.models.conversation import Conversation, ConversationType
from app.models.user import User
from app.models.message import SenderType
from app.schemas.chat import MessageOut
from app.services.chat.assistant_tools import (
    execute_prepare_order,
    execute_search,
    execute_view_product,
)
from app.services.chat.bot_engine import get_bot_engine


async def maybe_send_system_reply(
    db: Session,
    conv: Conversation,
    current_user: User,
    user_message: str,
    *,
    transport: str,
    broadcaster: Callable[[Conversation, MessageOut], Awaitable[None]],
) -> MessageOut | None:
    if conv.type != ConversationType.user_system:
        return None

    engine = get_bot_engine()
    history = list_by_conversation(db, conv.id, limit=20)
    decision = await engine.reply(
        current_user,
        user_message,
        history,
        transport=transport,
    )
    if decision.action == "search_products":
        query = (decision.search_query or user_message).strip()
        result = execute_search(db, query)
    elif decision.action == "view_product" and decision.product_id:
        result = execute_view_product(
            db,
            product_id=decision.product_id,
        )
    elif decision.action == "prepare_order" and decision.product_id:
        result = execute_prepare_order(
            db,
            conversation_id=conv.id,
            user=current_user,
            product_id=decision.product_id,
            quantity=decision.quantity,
        )
    else:
        result_text = decision.reply_text or "I could not complete that request."
        result = {"text": result_text, "assistant_payload": None}

    bot_msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=SenderType.bot,
        sender_id=None,
        content=result["text"] if isinstance(result, dict) else result.text,
        assistant_payload=(
            result["assistant_payload"]
            if isinstance(result, dict)
            else result.assistant_payload
        ),
    )
    touch_last_message(db, conv, bot_msg.created_at)
    out = MessageOut.model_validate(bot_msg)
    await broadcaster(conv, out)
    return out
