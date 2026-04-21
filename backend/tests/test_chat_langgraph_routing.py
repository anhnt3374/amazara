import asyncio
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.base  # noqa: F401
from app.api.v1.endpoints.chat import send_message_as_user
from app.api.v1.endpoints.chat_ws import _handle_send
from app.crud.conversation import get_or_create_user_store, get_or_create_user_system
from app.models.base import Base
from app.models.message import Message, SenderType
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import SendMessageRequest, WsClientSend


class DummyWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


class ChatLangGraphRoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = self.SessionLocal()

        self.user = User(
            email="user@example.com",
            username="buyer",
            password="hashed-password",
            fullname="Buyer Name",
        )
        self.store = Store(
            name="Store Name",
            slug="store-name",
            email="store@example.com",
            password_hash="hashed-store-password",
        )
        self.session.add_all([self.user, self.store])
        self.session.commit()
        self.session.refresh(self.user)
        self.session.refresh(self.store)

        self._reset_bot_engine()
        self.addCleanup(self._reset_bot_engine)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def _reset_bot_engine(self) -> None:
        import app.services.chat.bot_engine as bot_engine

        bot_engine._engine_cache = None

    def test_get_bot_engine_respects_bot_engine_setting(self) -> None:
        import app.services.chat.bot_engine as bot_engine
        from app.services.chat.langgraph_engine import LangGraphEngine

        original = bot_engine.settings.BOT_ENGINE
        try:
            bot_engine.settings.BOT_ENGINE = "placeholder"
            self.assertIsInstance(
                bot_engine.get_bot_engine(),
                bot_engine.StaticPlaceholderEngine,
            )
            self._reset_bot_engine()

            bot_engine.settings.BOT_ENGINE = "langgraph"
            self.assertIsInstance(bot_engine.get_bot_engine(), LangGraphEngine)
        finally:
            bot_engine.settings.BOT_ENGINE = original
            self._reset_bot_engine()

    def test_rest_handler_without_digits_returns_greeting(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content="hello assistant"),
                db=self.session,
                current_user=self.user,
            )
        )

        msgs = (
            self.session.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].sender_type, SenderType.user)
        self.assertEqual(msgs[0].content, "hello assistant")
        self.assertEqual(msgs[1].sender_type, SenderType.bot)
        self.assertEqual(msgs[1].content, "Hello! How can I help you today?")
        self.session.refresh(conv)
        self.assertEqual(conv.last_message_at, msgs[1].created_at)

    def test_rest_handler_with_digits_returns_sum(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content="sum 10 20 30"),
                db=self.session,
                current_user=self.user,
            )
        )

        bot_msg = (
            self.session.query(Message)
            .filter(
                Message.conversation_id == conv.id,
                Message.sender_type == SenderType.bot,
            )
            .one()
        )
        self.assertEqual(bot_msg.content, "The sum is 60.")

    def test_websocket_handler_with_digits_returns_sum(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)
        ws = DummyWebSocket()

        asyncio.run(
            _handle_send(
                ws,
                self.session,
                "user",
                self.user,
                WsClientSend(
                    type="send",
                    conversation_id=conv.id,
                    content="invoice 7 and 8 then 100",
                ),
            )
        )

        msgs = (
            self.session.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[1].sender_type, SenderType.bot)
        self.assertEqual(msgs[1].content, "The sum is 115.")
        self.assertEqual(ws.sent, [])

    def test_user_store_conversation_does_not_invoke_bot(self) -> None:
        conv = get_or_create_user_store(self.session, self.user.id, self.store.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content="hello seller 123"),
                db=self.session,
                current_user=self.user,
            )
        )

        msgs = (
            self.session.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].sender_type, SenderType.user)


if __name__ == "__main__":
    unittest.main()
