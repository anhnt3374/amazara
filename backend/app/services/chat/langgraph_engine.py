import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

try:
    from langsmith import traceable
except ImportError:  # pragma: no cover - dependency is installed in app runtime
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn

        return decorator

from app.models.message import Message
from app.models.user import User
from app.services.chat.bot_engine import BotEngine

GREETING_REPLY = "Hello! How can I help you today?"


class ChatGraphState(TypedDict, total=False):
    query: str
    numbers: list[int]
    history: list[str]
    response: str


def _extract_numbers(query: str) -> list[int]:
    return [int(match) for match in re.findall(r"-?\d+", query)]


class LangGraphEngine(BotEngine):
    def __init__(self) -> None:
        workflow = StateGraph(ChatGraphState)
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("greet_user", self._greet_user)
        workflow.add_node("sum_numbers", self._sum_numbers)
        workflow.add_edge(START, "route_query")
        workflow.add_conditional_edges(
            "route_query",
            self._pick_route,
            {
                "greet_user": "greet_user",
                "sum_numbers": "sum_numbers",
            },
        )
        workflow.add_edge("greet_user", END)
        workflow.add_edge("sum_numbers", END)
        self._graph = workflow.compile()

    async def reply(
        self,
        user: User,
        user_message: str,
        history: list[Message],
        *,
        transport: str = "unknown",
    ) -> str | None:
        conversation_id = history[-1].conversation_id if history else f"user:{user.id}"
        result = self._invoke_graph(
            {
                "query": user_message,
                "history": [message.content for message in history[-10:]],
            },
            conversation_id=conversation_id,
            user_id=user.id,
            transport=transport,
        )
        return result.get("response")

    def _route_query(self, state: ChatGraphState) -> ChatGraphState:
        return {"numbers": _extract_numbers(state["query"])}

    def _pick_route(self, state: ChatGraphState) -> str:
        return "sum_numbers" if state.get("numbers") else "greet_user"

    def _greet_user(self, state: ChatGraphState) -> ChatGraphState:
        return {"response": GREETING_REPLY}

    def _sum_numbers(self, state: ChatGraphState) -> ChatGraphState:
        total = sum(state.get("numbers", []))
        return {"response": f"The sum is {total}."}

    @traceable(name="chat.system.langgraph", run_type="chain")
    def _invoke_graph(
        self,
        state: ChatGraphState,
        *,
        conversation_id: str,
        user_id: str,
        transport: str,
    ) -> ChatGraphState:
        return self._graph.invoke(
            state,
            config={
                "configurable": {"thread_id": conversation_id},
                "metadata": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "transport": transport,
                    "engine": "langgraph",
                },
                "tags": ["chat", "system", "langgraph", transport],
            },
        )
