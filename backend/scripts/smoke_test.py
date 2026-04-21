import argparse
import asyncio
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.db.base  # noqa: F401
import websockets
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.conversation import Conversation
from app.models.favorite import Favorite
from app.models.message import Message
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.store import Store
from app.models.user import User

BASE_API = "http://127.0.0.1:8000/api/v1"
BACKEND_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:5173"
SMOKE_USER_PREFIX = "smoke.user."
SMOKE_STORE_PREFIX = "smoke.store."


@dataclass
class Result:
    name: str
    status: str
    detail: dict


class SmokeRunner:
    def __init__(self, *, keep_data: bool) -> None:
        self.keep_data = keep_data
        self.results: list[Result] = []
        self.products: list[dict] = []
        self.state: dict[str, str | int] = {}
        self.ts = str(int(time.time()))
        self.user_email = f"{SMOKE_USER_PREFIX}{self.ts}@example.com"
        self.user_pass = "SmokePass123!"
        self.store_email = f"{SMOKE_STORE_PREFIX}{self.ts}@example.com"
        self.store_pass = "SmokeStore123!"

    def record(self, name: str, status: str, detail: dict) -> None:
        self.results.append(Result(name=name, status=status, detail=detail))

    def normalize_headers(self, headers: dict) -> dict[str, str]:
        return {str(k).lower(): str(v) for k, v in headers.items()}

    def decode_body(self, raw: bytes, headers: dict[str, str]):
        content_type = headers.get("content-type", "")
        text = raw.decode(errors="replace") if raw else ""
        if "application/json" in content_type:
            try:
                return json.loads(text) if text else None
            except Exception:
                return text
        return text

    def req(
        self,
        method: str,
        path: str,
        *,
        data: dict | None = None,
        token: str | None = None,
        base: str = BASE_API,
    ):
        url = path if path.startswith("http") else f"{base}{path}"
        headers: dict[str, str] = {}
        payload = None
        if data is not None:
            payload = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
                hdrs = self.normalize_headers(dict(response.headers))
                return response.status, self.decode_body(raw, hdrs), hdrs
        except urllib.error.HTTPError as exc:
            hdrs = self.normalize_headers(dict(exc.headers))
            raw = exc.read()
            return exc.code, self.decode_body(raw, hdrs), hdrs

    def check(self, cond: bool, name: str, detail_ok: dict, detail_fail: dict) -> bool:
        self.record(name, "PASS" if cond else "FAIL", detail_ok if cond else detail_fail)
        return cond

    async def ws_check(self, token: str, conversation_id: str) -> tuple[dict, dict]:
        url = f"ws://127.0.0.1:8000/api/v1/ws/chat?token={urllib.parse.quote(token)}"
        async with websockets.connect(url, open_timeout=10, close_timeout=5) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "send",
                        "conversation_id": conversation_id,
                        "content": "ws 7 8",
                    }
                )
            )
            first = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            second = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            return first, second

    def run(self) -> int:
        try:
            cleanup_smoke_data()
            self.run_baseline()
            self.run_user_auth()
            self.run_catalog()
            self.run_addresses()
            self.run_favorites()
            self.run_cart_and_orders()
            self.run_system_chat()
            self.run_store_auth_and_chat()
        finally:
            if not self.keep_data:
                cleanup_smoke_data()

        print(json.dumps([asdict(result) for result in self.results], ensure_ascii=False, indent=2))
        return 1 if any(result.status == "FAIL" for result in self.results) else 0

    def run_baseline(self) -> None:
        status, body, _ = self.req("GET", "/health", base=BACKEND_BASE)
        self.check(
            status == 200 and body == {"status": "ok"},
            "backend.health",
            {"status": "ok"},
            {"status": status, "body": body},
        )

        for route in ["/", "/list", "/login", "/signup", "/messages", "/store/messages"]:
            status, body, headers = self.req("GET", route, base=FRONTEND_BASE)
            ok = (
                status == 200
                and "text/html" in headers.get("content-type", "")
                and "<div id=\"root\"></div>" in body
            )
            self.record(
                f"frontend.route:{route}",
                "PASS" if ok else "FAIL",
                {"status": status, "content_type": headers.get("content-type", "")},
            )

    def run_user_auth(self) -> None:
        status, body, _ = self.req(
            "POST",
            "/auth/register",
            data={
                "fullname": "Smoke User",
                "username": f"smokeuser{self.ts}",
                "email": self.user_email,
                "password": self.user_pass,
            },
        )
        if self.check(
            status == 201 and isinstance(body, dict) and body.get("email") == self.user_email,
            "auth.user_register",
            body,
            {"status": status, "body": body},
        ):
            self.state["user_id"] = body["id"]

        status, body, _ = self.req(
            "POST",
            "/auth/login",
            data={"email": self.user_email, "password": self.user_pass},
        )
        if self.check(
            status == 200 and isinstance(body, dict) and body.get("access_token"),
            "auth.user_login",
            {"token_type": body.get("token_type")},
            {"status": status, "body": body},
        ):
            self.state["user_token"] = body["access_token"]

        user_token = self.state.get("user_token")
        if not isinstance(user_token, str):
            return

        status, body, _ = self.req("GET", "/auth/me", token=user_token)
        self.check(
            status == 200 and isinstance(body, dict) and body.get("type") == "user",
            "auth.user_me",
            {"id": body.get("id"), "display_name": body.get("display_name")},
            {"status": status, "body": body},
        )

    def run_catalog(self) -> None:
        status, body, _ = self.req("GET", "/products/search?page=1")
        self.products = body.get("products", []) if isinstance(body, dict) else []
        if not self.products:
            self.record(
                "catalog.product_search",
                "BLOCKED",
                {"reason": "No products returned from /products/search"},
            )
            return

        product = self.products[0]
        self.state["product_id"] = product["id"]
        self.state["product_price"] = product["price"]
        self.state["product_discount"] = product["discount"]
        self.record(
            "catalog.product_search",
            "PASS",
            {"count": len(self.products), "sample_product_id": product["id"]},
        )

        user_token = self.state.get("user_token")
        status, body, _ = self.req(
            "GET",
            f"/products/{product['id']}",
            token=user_token if isinstance(user_token, str) else None,
        )
        self.check(
            status == 200 and isinstance(body, dict) and body.get("id") == product["id"],
            "catalog.product_detail",
            {"product_id": product["id"], "store_id": body.get("store_id")},
            {"status": status, "body": body},
        )

    def run_addresses(self) -> None:
        user_token = self.state.get("user_token")
        if not isinstance(user_token, str):
            self.record("addresses", "BLOCKED", {"reason": "Missing user token"})
            return

        status, body, _ = self.req(
            "POST",
            "/addresses/",
            data={
                "place": "123 Smoke Street, Test Ward",
                "phone": "0900000000",
                "client_name": "Smoke User",
            },
            token=user_token,
        )
        address_id = body["id"] if status == 201 and isinstance(body, dict) else None
        self.record(
            "addresses.create",
            "PASS" if address_id else "FAIL",
            body if address_id else {"status": status, "body": body},
        )
        if not address_id:
            return
        self.state["address_id"] = address_id

        status, body, _ = self.req("GET", "/addresses/", token=user_token)
        listed = isinstance(body, list) and any(item.get("id") == address_id for item in body)
        self.record(
            "addresses.list",
            "PASS" if (status == 200 and listed) else "FAIL",
            {"status": status, "count": len(body) if isinstance(body, list) else None},
        )

    def run_favorites(self) -> None:
        user_token = self.state.get("user_token")
        product_id = self.state.get("product_id")
        if not isinstance(user_token, str) or not isinstance(product_id, str):
            self.record(
                "favorites",
                "BLOCKED",
                {"reason": "Missing user token or product"},
            )
            return

        status, body, _ = self.req(
            "POST",
            "/favorites/",
            data={"product_id": product_id},
            token=user_token,
        )
        self.record("favorites.add", "PASS" if status == 201 else "FAIL", {"status": status, "body": body})

        status, body, _ = self.req("GET", "/favorites/", token=user_token)
        listed = isinstance(body, list) and any(item.get("id") == product_id for item in body)
        self.record(
            "favorites.list",
            "PASS" if (status == 200 and listed) else "FAIL",
            {"status": status, "count": len(body) if isinstance(body, list) else None},
        )

        status, body, _ = self.req("DELETE", f"/favorites/{product_id}", token=user_token)
        self.record(
            "favorites.delete",
            "PASS" if status == 204 else "FAIL",
            {"status": status, "body": body},
        )

    def run_cart_and_orders(self) -> None:
        user_token = self.state.get("user_token")
        product_id = self.state.get("product_id")
        product_price = self.state.get("product_price")
        product_discount = self.state.get("product_discount")
        address_id = self.state.get("address_id")
        if not all(
            [
                isinstance(user_token, str),
                isinstance(product_id, str),
                isinstance(product_price, (int, float)),
                isinstance(product_discount, int),
                isinstance(address_id, str),
            ]
        ):
            self.record(
                "commerce",
                "BLOCKED",
                {"reason": "Missing cart/order prerequisites"},
            )
            return

        status, body, _ = self.req(
            "POST",
            "/cart/",
            data={"product_id": product_id, "quantity": 1, "notes": "smoke"},
            token=user_token,
        )
        cart_item_id = body["id"] if status == 201 and isinstance(body, dict) else None
        self.record(
            "cart.add",
            "PASS" if cart_item_id else "FAIL",
            body if cart_item_id else {"status": status, "body": body},
        )
        if not cart_item_id:
            return

        status, body, _ = self.req("GET", "/cart/", token=user_token)
        items = body.get("items", []) if isinstance(body, dict) else []
        listed = any(item.get("id") == cart_item_id for item in items)
        self.record(
            "cart.list",
            "PASS" if (status == 200 and listed) else "FAIL",
            {"status": status, "total_count": body.get("total_count") if isinstance(body, dict) else None},
        )

        status, body, _ = self.req(
            "PATCH",
            f"/cart/{cart_item_id}",
            data={"quantity": 2, "notes": "smoke updated"},
            token=user_token,
        )
        self.record(
            "cart.update",
            "PASS" if (status == 200 and isinstance(body, dict) and body.get("quantity") == 2) else "FAIL",
            {"status": status, "body": body},
        )

        unit_price = int(product_price * (100 - product_discount) / 100)
        total_amount = unit_price * 2
        status, body, _ = self.req(
            "POST",
            "/orders/",
            data={
                "place": "123 Smoke Street, Test Ward",
                "phone": "0900000000",
                "client_name": "Smoke User",
                "total_amount": total_amount,
                "note": "smoke order",
                "items": [
                    {
                        "product_id": product_id,
                        "product_name": self.products[0]["name"],
                        "quantity": 2,
                        "price": unit_price,
                        "notes": "smoke updated",
                    }
                ],
                "cart_item_ids": [cart_item_id],
            },
            token=user_token,
        )
        order_id = body["id"] if status == 201 and isinstance(body, dict) else None
        self.record(
            "orders.create",
            "PASS" if order_id else "FAIL",
            body if order_id else {"status": status, "body": body},
        )
        if not order_id:
            return

        status, body, _ = self.req("GET", "/orders/", token=user_token)
        listed = isinstance(body, list) and any(item.get("id") == order_id for item in body)
        self.record(
            "orders.list",
            "PASS" if (status == 200 and listed) else "FAIL",
            {"status": status, "count": len(body) if isinstance(body, list) else None},
        )

        status, body, _ = self.req("GET", f"/orders/{order_id}", token=user_token)
        self.record(
            "orders.detail",
            "PASS" if (status == 200 and isinstance(body, dict) and body.get("id") == order_id) else "FAIL",
            {"status": status, "body": body},
        )

    def run_system_chat(self) -> None:
        user_token = self.state.get("user_token")
        if not isinstance(user_token, str):
            self.record("chat", "BLOCKED", {"reason": "Missing user token"})
            return

        system_conversation_id = None
        status, body, _ = self.req("GET", "/chats", token=user_token)
        if status == 200 and isinstance(body, list):
            self.record("chat.user_list", "PASS", {"count": len(body)})
            for conv in body:
                if conv.get("type") == "user_system":
                    system_conversation_id = conv["id"]
                    break
        else:
            self.record("chat.user_list", "FAIL", {"status": status, "body": body})

        if not system_conversation_id:
            return

        self.req(
            "POST",
            f"/chats/{system_conversation_id}/messages",
            data={"content": "hello smoke"},
            token=user_token,
        )
        self.req(
            "POST",
            f"/chats/{system_conversation_id}/messages",
            data={"content": "sum 10 20 30"},
            token=user_token,
        )
        status, body, _ = self.req(
            "GET",
            f"/chats/{system_conversation_id}/messages?limit=10",
            token=user_token,
        )
        contents = [item.get("content") for item in body] if isinstance(body, list) else []
        self.record(
            "chat.system_history",
            "PASS"
            if (status == 200 and "Hello! How can I help you today?" in contents and "The sum is 60." in contents)
            else "FAIL",
            {"status": status, "tail": contents[-4:]},
        )

        try:
            first, second = asyncio.run(self.ws_check(user_token, system_conversation_id))
            ok = (
                first.get("message", {}).get("sender_type") == "user"
                and second.get("message", {}).get("content") == "The sum is 15."
            )
            self.record(
                "chat.websocket",
                "PASS" if ok else "FAIL",
                {
                    "first_sender": first.get("message", {}).get("sender_type"),
                    "second_content": second.get("message", {}).get("content"),
                },
            )
        except Exception as exc:
            self.record("chat.websocket", "FAIL", {"error": str(exc)})

    def run_store_auth_and_chat(self) -> None:
        status, body, _ = self.req(
            "POST",
            "/auth/register-store",
            data={
                "name": f"Smoke Store {self.ts}",
                "email": self.store_email,
                "password": self.store_pass,
                "description": "Smoke store account",
            },
        )
        store_token = body.get("access_token") if status == 201 and isinstance(body, dict) else None
        self.record(
            "auth.store_register",
            "PASS" if store_token else "FAIL",
            {"status": status, "body": {"token_type": body.get("token_type")} if store_token else body},
        )
        if not isinstance(store_token, str):
            return

        user_token = self.state.get("user_token")
        status, body, _ = self.req("GET", "/auth/me", token=store_token)
        store_id = body.get("id") if status == 200 and isinstance(body, dict) else None
        self.record(
            "auth.store_me",
            "PASS" if store_id else "FAIL",
            {"status": status, "body": body},
        )
        if not isinstance(store_id, str) or not isinstance(user_token, str):
            return

        status, body, _ = self.req("POST", f"/chats/with-store/{store_id}", token=user_token)
        convo_id = body.get("id") if status == 200 and isinstance(body, dict) else None
        self.record(
            "chat.user_store_open",
            "PASS" if convo_id else "FAIL",
            {"status": status, "body": body},
        )
        if not isinstance(convo_id, str):
            return

        self.req(
            "POST",
            f"/chats/{convo_id}/messages",
            data={"content": "hello new store"},
            token=user_token,
        )

        status, body, _ = self.req("GET", "/chats/store", token=store_token)
        listed = isinstance(body, list) and any(item.get("id") == convo_id for item in body)
        self.record(
            "chat.store_list",
            "PASS" if (status == 200 and listed) else "FAIL",
            {"status": status, "count": len(body) if isinstance(body, list) else None},
        )

        status, body, _ = self.req(
            "POST",
            f"/chats/store/{convo_id}/messages",
            data={"content": "store reply smoke"},
            token=store_token,
        )
        self.record(
            "chat.user_store_send_store",
            "PASS" if status == 200 else "FAIL",
            {"status": status, "body": body},
        )

        status, body, _ = self.req("GET", f"/chats/{convo_id}/messages?limit=10", token=user_token)
        reply_ok = (
            status == 200
            and isinstance(body, list)
            and any(item.get("content") == "store reply smoke" for item in body)
        )
        self.record(
            "chat.user_store_history_after_reply",
            "PASS" if reply_ok else "FAIL",
            {"status": status, "tail": body[-3:] if isinstance(body, list) else body},
        )


def cleanup_smoke_data() -> dict[str, int]:
    session: Session = SessionLocal()
    try:
        smoke_users = session.query(User).filter(User.email.like(f"{SMOKE_USER_PREFIX}%")).all()
        smoke_stores = session.query(Store).filter(Store.email.like(f"{SMOKE_STORE_PREFIX}%")).all()
        user_ids = [user.id for user in smoke_users]
        store_ids = [store.id for store in smoke_stores]

        conversation_ids: list[str] = []
        if user_ids or store_ids:
            conversations = session.query(Conversation)
            if user_ids:
                conversations = conversations.filter(Conversation.user_id.in_(user_ids))
            if store_ids:
                conversations = conversations.union(
                    session.query(Conversation).filter(Conversation.store_id.in_(store_ids))
                )
            conversation_ids = [conversation.id for conversation in conversations.all()]

        order_ids = [order.id for order in session.query(Order).filter(Order.user_id.in_(user_ids)).all()] if user_ids else []

        deleted = {
            "messages": 0,
            "conversations": 0,
            "order_items": 0,
            "orders": 0,
            "favorites": 0,
            "cart_items": 0,
            "addresses": 0,
            "users": 0,
            "stores": 0,
        }

        if conversation_ids:
            deleted["messages"] = (
                session.query(Message)
                .filter(Message.conversation_id.in_(conversation_ids))
                .delete(synchronize_session=False)
            )
            deleted["conversations"] = (
                session.query(Conversation)
                .filter(Conversation.id.in_(conversation_ids))
                .delete(synchronize_session=False)
            )

        if order_ids:
            deleted["order_items"] = (
                session.query(OrderItem)
                .filter(OrderItem.order_id.in_(order_ids))
                .delete(synchronize_session=False)
            )
            deleted["orders"] = (
                session.query(Order)
                .filter(Order.id.in_(order_ids))
                .delete(synchronize_session=False)
            )

        if user_ids:
            deleted["favorites"] = (
                session.query(Favorite)
                .filter(Favorite.user_id.in_(user_ids))
                .delete(synchronize_session=False)
            )
            deleted["cart_items"] = (
                session.query(CartItem)
                .filter(CartItem.user_id.in_(user_ids))
                .delete(synchronize_session=False)
            )
            deleted["addresses"] = (
                session.query(Address)
                .filter(Address.user_id.in_(user_ids))
                .delete(synchronize_session=False)
            )
            deleted["users"] = (
                session.query(User)
                .filter(User.id.in_(user_ids))
                .delete(synchronize_session=False)
            )

        if store_ids:
            deleted["stores"] = (
                session.query(Store)
                .filter(Store.id.in_(store_ids))
                .delete(synchronize_session=False)
            )

        session.commit()
        return deleted
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or clean smoke test data.")
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Delete smoke test data and exit.",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Keep generated smoke test data after the run.",
    )
    args = parser.parse_args()

    if args.cleanup_only:
        deleted = cleanup_smoke_data()
        print(json.dumps({"cleanup": deleted}, ensure_ascii=False, indent=2))
        return 0

    runner = SmokeRunner(keep_data=args.keep_data)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
