from abc import ABC, abstractmethod
import re

from app.core.config import settings
from app.models.message import Message
from app.models.user import User
from app.services.chat.assistant_types import AssistantDecision


class BotEngine(ABC):
    """Strategy interface for replying to user messages in the system conversation.

    Swap the concrete implementation via `BOT_ENGINE` env var. Future
    implementations (e.g., LangGraphEngine) plug in here without touching the
    endpoint / websocket layer.
    """

    @abstractmethod
    async def reply(
        self,
        user: User,
        user_message: str,
        history: list[Message],
        *,
        transport: str = "unknown",
    ) -> AssistantDecision:
        """Return the assistant decision for the next backend action."""


PRODUCT_ID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
QUANTITY_RE = re.compile(
    r"\border\s+(\d+)\b|\bbuy\s+(\d+)\b|\bqty\s*(\d+)\b|\bquantity\s*(\d+)\b"
)


def _extract_quantity(text: str) -> int:
    match = QUANTITY_RE.search(text)
    if not match:
        return 1
    for group in match.groups():
        if group:
            return max(int(group), 1)
    return 1


class StaticStubEngine(BotEngine):
    async def reply(self, user, user_message, history, *, transport="unknown"):
        product_match = PRODUCT_ID_RE.search(user_message)
        if product_match:
            return AssistantDecision(
                action="prepare_order",
                product_id=product_match.group(0),
                quantity=_extract_quantity(user_message),
            )
        query = user_message.strip()
        if query:
            return AssistantDecision(action="search_products", search_query=query)
        return AssistantDecision(
            action="plain_reply",
            reply_text="Please send a message so I can help.",
        )


StaticPlaceholderEngine = StaticStubEngine


_engine_cache: BotEngine | None = None


def get_bot_engine() -> BotEngine:
    global _engine_cache
    if _engine_cache is not None:
        return _engine_cache
    name = getattr(settings, "BOT_ENGINE", "stub")
    if name == "langgraph":
        from app.services.chat.langgraph_engine import LangGraphEngine

        _engine_cache = LangGraphEngine()
    elif name == "groq" and settings.GROQ_API_KEY:
        from app.services.chat.groq_engine import GroqBotEngine

        _engine_cache = GroqBotEngine()
    else:
        _engine_cache = StaticStubEngine()
    return _engine_cache
