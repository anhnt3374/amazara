import asyncio
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.base  # noqa: F401
from app.api.v1.endpoints.chat import send_message_as_user, submit_assistant_action
from app.crud.conversation import get_or_create_user_system
from app.models.address import Address
from app.models.base import Base
from app.models.brand import Brand
from app.models.category import Category
from app.models.message import Message, SenderType
from app.models.order import Order
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import AssistantActionRequest, SendMessageRequest


class ChatAssistantFlowTest(unittest.TestCase):
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
        self.brand = Brand(name="Brand Name")
        self.category = Category(name="Category Name", brand=self.brand)
        self.product = Product(
            name="Running Shoes",
            description="lightweight running shoes for daily training",
            price=120000,
            discount=10,
            stock=8,
            image="https://example.com/shoe.jpg",
            category=self.category,
            store=self.store,
        )
        self.session.add_all(
            [self.user, self.store, self.brand, self.category, self.product]
        )
        self.session.commit()
        self.session.refresh(self.user)
        self.session.refresh(self.product)

        self._reset_bot_engine()
        self._set_bot_engine("stub")
        self.addCleanup(self._reset_bot_engine)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def _reset_bot_engine(self) -> None:
        import app.services.chat.bot_engine as bot_engine

        bot_engine._engine_cache = None

    def _set_bot_engine(self, value: str) -> None:
        import app.services.chat.bot_engine as bot_engine

        bot_engine.settings.BOT_ENGINE = value
        self._reset_bot_engine()

    def _create_address(self) -> None:
        self.session.add(
            Address(
                user_id=self.user.id,
                place="123 Test Street",
                phone="+84 900 000 000",
                client_name="Buyer Name",
            )
        )
        self.session.commit()

    def test_search_query_returns_product_carousel_payload(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content="running shoes"),
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
        self.assertEqual(msgs[1].sender_type, SenderType.bot)
        self.assertIsNotNone(msgs[1].assistant_payload)
        payload = msgs[1].assistant_payload
        self.assertEqual(payload["type"], "product_carousel")
        self.assertEqual(payload["query"], "running shoes")
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 20)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["product_id"], self.product.id)

    def test_order_request_returns_confirmation_payload_with_draft(self) -> None:
        self._create_address()
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content=f"order 2 {self.product.id}"),
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
        self.assertIsNotNone(bot_msg.assistant_payload)
        payload = bot_msg.assistant_payload
        self.assertEqual(payload["type"], "order_confirmation")
        self.assertEqual(payload["quantity"], 2)
        self.assertEqual(payload["product"]["product_id"], self.product.id)
        self.assertIn("draft_id", payload["action"])

    def test_order_request_without_saved_address_returns_guidance(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content=f"order {self.product.id}"),
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
        self.assertIsNone(bot_msg.assistant_payload)
        self.assertIn("address", bot_msg.content.lower())

    def test_confirm_action_creates_order_and_result_payload(self) -> None:
        self._create_address()
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content=f"order 3 {self.product.id}"),
                db=self.session,
                current_user=self.user,
            )
        )

        confirm_msg = (
            self.session.query(Message)
            .filter(
                Message.conversation_id == conv.id,
                Message.sender_type == SenderType.bot,
            )
            .one()
        )
        draft_id = confirm_msg.assistant_payload["action"]["draft_id"]

        result = asyncio.run(
            submit_assistant_action(
                conv.id,
                AssistantActionRequest(
                    action_id="confirm_order",
                    data={"draft_id": draft_id},
                ),
                db=self.session,
                current_user=self.user,
            )
        )

        orders = self.session.query(Order).all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].order_items[0].product_id, self.product.id)
        self.assertEqual(orders[0].order_items[0].quantity, 3)
        self.assertIsNotNone(result.assistant_payload)
        self.assertEqual(result.assistant_payload["type"], "order_result")
        self.assertEqual(result.assistant_payload["order"]["order_id"], orders[0].id)

    def test_view_product_request_returns_product_info_payload(self) -> None:
        conv = get_or_create_user_system(self.session, self.user.id)

        asyncio.run(
            send_message_as_user(
                conv.id,
                SendMessageRequest(content=f"show product {self.product.id}"),
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
        self.assertIsNotNone(bot_msg.assistant_payload)
        payload = bot_msg.assistant_payload
        self.assertEqual(payload["type"], "product_info")
        self.assertEqual(payload["product"]["product_id"], self.product.id)
        self.assertEqual(payload["product"]["name"], self.product.name)

    def test_groq_response_without_action_is_normalized_to_view_product(self) -> None:
        self._set_bot_engine("groq")
        conv = get_or_create_user_system(self.session, self.user.id)
        product_id = self.product.id

        async def fake_reply(*args, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                f'{{"product_id":"{self.product.id}","quantity":1}}'
                            )
                        }
                    }
                ]
            }

        class FakeResponse:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            async def json(self):
                return await fake_reply()

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, *args, **kwargs):
                return FakeResponse()

        with patch("app.services.chat.groq_engine.aiohttp.ClientSession", return_value=FakeSession()):
            asyncio.run(
                send_message_as_user(
                    conv.id,
                    SendMessageRequest(content=f"order {self.product.id}"),
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
        self.assertIsNotNone(bot_msg.assistant_payload)
        self.assertEqual(bot_msg.assistant_payload["type"], "product_info")
        self.assertEqual(bot_msg.assistant_payload["product"]["product_id"], product_id)

    def test_groq_prepare_order_action_still_returns_order_confirmation(self) -> None:
        self._create_address()
        self._set_bot_engine("groq")
        conv = get_or_create_user_system(self.session, self.user.id)
        product_id = self.product.id

        class FakeResponse:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            async def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    f'{{"action":"prepare_order","product_id":"{product_id}","quantity":2}}'
                                )
                            }
                        }
                    ]
                }

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, *args, **kwargs):
                return FakeResponse()

        with patch(
            "app.services.chat.groq_engine.aiohttp.ClientSession",
            return_value=FakeSession(),
        ):
            asyncio.run(
                send_message_as_user(
                    conv.id,
                    SendMessageRequest(content=f"order 2 {self.product.id}"),
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
        self.assertEqual(bot_msg.assistant_payload["type"], "order_confirmation")
        self.assertEqual(bot_msg.assistant_payload["quantity"], 2)

    def test_groq_invalid_payload_falls_back_to_plain_reply(self) -> None:
        self._set_bot_engine("groq")
        conv = get_or_create_user_system(self.session, self.user.id)

        class FakeResponse:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            async def json(self):
                return {"choices": [{"message": {"content": '{"quantity":"abc"}'}}]}

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, *args, **kwargs):
                return FakeResponse()

        with patch("app.services.chat.groq_engine.aiohttp.ClientSession", return_value=FakeSession()):
            asyncio.run(
                send_message_as_user(
                    conv.id,
                    SendMessageRequest(content="help"),
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
        self.assertIsNone(bot_msg.assistant_payload)
        self.assertIn("could not understand", bot_msg.content.lower())


if __name__ == "__main__":
    unittest.main()
