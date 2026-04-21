from abc import ABC, abstractmethod

from app.core.config import settings
from app.models.message import Message
from app.models.user import User


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
    ) -> str | None:
        """Return bot reply text, or None to skip sending a reply."""


class StaticPlaceholderEngine(BotEngine):
    MESSAGE = (
        "This feature is still being finalized — feel free to ask and we'll "
        "bring in the real assistant soon."
    )

    async def reply(self, user, user_message, history, *, transport="unknown"):
        return self.MESSAGE


_engine_cache: BotEngine | None = None


def get_bot_engine() -> BotEngine:
    global _engine_cache
    if _engine_cache is not None:
        return _engine_cache
    name = getattr(settings, "BOT_ENGINE", "placeholder")
    if name == "langgraph":
        from app.services.chat.langgraph_engine import LangGraphEngine

        _engine_cache = LangGraphEngine()
    else:
        _engine_cache = StaticPlaceholderEngine()
    return _engine_cache
