import json

import aiohttp
from pydantic import ValidationError

from app.core.config import settings
from app.models.message import Message
from app.models.user import User
from app.services.chat.assistant_types import AssistantDecision
from app.services.chat.bot_engine import BotEngine

SYSTEM_PROMPT = """
You are an e-commerce assistant.
You must return JSON only.

Choose exactly one action:
- search_products: when the user is searching for products
- view_product: when the user wants product details for a product code
- prepare_order: when the user clearly wants to order a product by product code
- plain_reply: for everything else

Rules:
- Product code is the existing product ID and must be copied exactly from the user message.
- Extract a simple quantity when present, otherwise use 1.
- Never invent products, prices, addresses, or order IDs.
- For search_products, set search_query to the user's search phrase.
- For view_product, set product_id.
- For prepare_order, set product_id and quantity.
- For plain_reply, set reply_text.
""".strip()


def _normalize_decision_payload(parsed: dict) -> dict:
    normalized = dict(parsed)
    if "action" not in normalized:
        if normalized.get("product_id"):
            normalized["action"] = "view_product"
        elif normalized.get("search_query"):
            normalized["action"] = "search_products"
        elif normalized.get("reply_text"):
            normalized["action"] = "plain_reply"
    quantity = normalized.get("quantity")
    if quantity is not None:
        try:
            normalized["quantity"] = max(int(quantity), 1)
        except (TypeError, ValueError):
            normalized.pop("quantity", None)
    return normalized


def _safe_plain_reply() -> AssistantDecision:
    return AssistantDecision(
        action="plain_reply",
        reply_text="I could not understand that request. Please try again.",
    )


class GroqBotEngine(BotEngine):
    async def reply(
        self,
        user: User,
        user_message: str,
        history: list[Message],
        *,
        transport: str = "unknown",
    ) -> AssistantDecision:
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_id": user.id,
                            "transport": transport,
                            "message": user_message,
                            "recent_history": [
                                item.content for item in history[-6:]
                            ],
                        }
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "reasoning_effort": "medium",
        }
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.GROQ_BASE_URL,
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()
        content = data["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return _safe_plain_reply()
        if not isinstance(parsed, dict):
            return _safe_plain_reply()
        normalized = _normalize_decision_payload(parsed)
        try:
            return AssistantDecision.model_validate(normalized)
        except ValidationError:
            return _safe_plain_reply()
