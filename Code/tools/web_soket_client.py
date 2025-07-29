import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Final

import websocket

logger = logging.getLogger(__name__)


WEBSOCKET_PING: Final[bytes] = b"\x01"
WEBSOCKET_PONG: Final[bytes] = b"\x02"


class WebSocketClient:
    _ws: websocket.WebSocketApp | None = None
    _url: str = ""

    _auth: str = ""

    _listener_thread: threading.Thread | None = None
    _running: bool = False

    _handlers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event: str, handler: Callable[[Any], None]) -> None:
        cls._handlers[event].append(handler)

    @classmethod
    def unsubscribe(cls, event: str, handler: Callable[[Any], None]) -> None:
        cls._handlers[event].remove(handler)

    @classmethod
    def connect(cls, url: str, auth: str) -> None:
        cls._url = url
        cls._ws = websocket.WebSocketApp(
            url,
            on_message=cls._on_message,
            on_open=cls._on_open,
            on_close=cls._on_close,
            on_error=cls._on_error,
        )

        cls._running = True
        cls._auth = auth
        cls._listener_thread = threading.Thread(target=cls._ws.run_forever, name='WebSocketClient', daemon=True)
        cls._listener_thread.start()

        time.sleep(1)

    @classmethod
    def disconnect(cls) -> None:
        cls._running = False
        if cls._ws:
            cls._ws.close()

        cls._ws = None
        cls._listener_thread = None

    @classmethod
    def _on_open(cls, ws):
        pass

    @classmethod
    def _on_close(cls, ws, close_status_code, close_msg):
        pass

    @classmethod
    def _on_error(cls, ws, error):
        logger.error(f"{error}")

    @classmethod
    def _on_message(cls, ws: websocket.WebSocket, message: str):
        if message == WEBSOCKET_PING:
            ws.send_bytes(WEBSOCKET_PONG)
            return

        if message == "auth request":
            ws.send_text(cls._auth)
            return

        try:
            data = json.loads(message)
            cls.handle_message(data)

        except json.JSONDecodeError:
            pass

    @classmethod
    def handle_message(cls, data: dict) -> None:
        event = data.pop("event")
        if not event:
            return

        cls._dispatch_event(event, data)

    @classmethod
    def _dispatch_event(cls, event: str, data: dict) -> None:
        for handler in cls._handlers.get(event, []):
            try:
                handler(**data)  # type: ignore

            except Exception as e:
                logger.error(f"Error in handler for {event}: {e}")
