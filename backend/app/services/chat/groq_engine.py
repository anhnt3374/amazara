import json

import aiohttp

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
- prepare_order: when the user clearly wants to order a product by product code
- plain_reply: for everything else

Rules:
- Product code is the existing product ID and must be copied exactly from the user message.
- Extract a simple quantity when present, otherwise use 1.
- Never invent products, prices, addresses, or order IDs.
- For search_products, set search_query to the user's search phrase.
- For prepare_order, set product_id and quantity.
- For plain_reply, set reply_text.
""".strip()


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
        parsed = json.loads(content)
        return AssistantDecision.model_validate(parsed)
