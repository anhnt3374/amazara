from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.models.conversation import ConversationType
from app.models.message import MessageRefType, SenderType


class PartnerInfo(BaseModel):
    id: str | None
    display_name: str
    avatar: str | None = None

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_type: SenderType
    sender_id: str | None
    content: str
    ref_type: MessageRefType | None
    ref_id: str | None
    ref_payload: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    type: ConversationType
    user_id: str
    store_id: str | None
    partner: PartnerInfo
    last_message: MessageOut | None = None
    unread_count: int = 0
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
    ref_type: MessageRefType | None = None
    ref_id: str | None = None


class WsClientSend(BaseModel):
    type: Literal["send"]
    conversation_id: str
    content: str
    ref_type: MessageRefType | None = None
    ref_id: str | None = None


class WsClientRead(BaseModel):
    type: Literal["read"]
    conversation_id: str


class WsServerMessage(BaseModel):
    type: Literal["message"] = "message"
    conversation_id: str
    message: MessageOut


class WsServerError(BaseModel):
    type: Literal["error"] = "error"
    detail: str
