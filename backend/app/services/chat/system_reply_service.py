from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session

from app.crud.conversation import touch_last_message
from app.crud.message import create_message, list_by_conversation
from app.models.conversation import Conversation, ConversationType
from app.models.user import User
from app.models.message import SenderType
from app.schemas.chat import MessageOut
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
    reply_text = await engine.reply(
        current_user,
        user_message,
        history,
        transport=transport,
    )
    if not reply_text:
        return None

    bot_msg = create_message(
        db,
        conversation_id=conv.id,
        sender_type=SenderType.bot,
        sender_id=None,
        content=reply_text,
    )
    touch_last_message(db, conv, bot_msg.created_at)
    out = MessageOut.model_validate(bot_msg)
    await broadcaster(conv, out)
    return out
