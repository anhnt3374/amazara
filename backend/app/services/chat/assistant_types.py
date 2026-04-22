from typing import Literal

from pydantic import BaseModel, Field


class AssistantDecision(BaseModel):
    action: Literal["search_products", "prepare_order", "plain_reply"]
    reply_text: str | None = None
    search_query: str | None = None
    product_id: str | None = None
    quantity: int = 1


class AssistantExecutionResult(BaseModel):
    text: str
    assistant_payload: dict | None = None
