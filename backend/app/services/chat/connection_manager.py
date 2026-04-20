import asyncio
from typing import Literal

from fastapi import WebSocket

AccountType = Literal["user", "store"]


class ConnectionManager:
    """In-memory WebSocket connection registry.

    Keyed by (account_type, account_id). A single account may have multiple
    sockets open (e.g., multiple tabs); every live socket receives broadcasts.

    This implementation is per-process. For multi-worker deployments, swap the
    broadcast path for a Redis pub/sub or similar fan-out.
    """

    def __init__(self) -> None:
        self._conns: dict[tuple[AccountType, str], set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self, account_type: AccountType, account_id: str, ws: WebSocket
    ) -> None:
        async with self._lock:
            self._conns.setdefault((account_type, account_id), set()).add(ws)

    async def disconnect(
        self, account_type: AccountType, account_id: str, ws: WebSocket
    ) -> None:
        async with self._lock:
            bucket = self._conns.get((account_type, account_id))
            if not bucket:
                return
            bucket.discard(ws)
            if not bucket:
                self._conns.pop((account_type, account_id), None)

    async def send_to(
        self, account_type: AccountType, account_id: str, payload: dict
    ) -> None:
        async with self._lock:
            targets = list(self._conns.get((account_type, account_id), ()))
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                # Best-effort; disconnects will be cleaned up by the endpoint.
                continue


_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
