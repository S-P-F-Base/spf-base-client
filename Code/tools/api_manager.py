import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from requests import Response, Session

from .config import Config
from .web_soket_client import WebSocketClient

logger = logging.getLogger(__name__)


class APIError(ValueError):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


class UserAccessTranslate(Enum):
    ALL_ACCESS = "Полные права"

    READ_USER = "Смотреть данные других пользователей"
    CONTROL_USER = "Управлять данными пользователями"

    READ_GAME_SERVER = "Смотреть игровой сервер"
    CONTROL_GAME_SERVER = "Управлять игровым сервером"

    READ_PAYMENT = "Читать чеки"
    GIVE_PAYMENT = "Выдавать чеки"
    CONTROL_PAYMENT = "Управлять донатом"

    READ_PLAYER = "Читать данные игрока"
    CONTROL_PLAYER = "Управлять данными игроков"

    READ_LOGS = "Читать логи"
    CONTROL_LOGS = "Управлять логами"

    SERVICE_CONTROL = "Управлять услугами"

    LORE_CHAR_CONTROL = "Управлять лорными персонажами"


class LogTypeTranslate(Enum):
    LOGIN = "Вошёл"
    LOGOUT = "Вышел"

    USER_CREATE = "Создал пользователя"
    USER_DELETE = "Удалил пользователя"
    USER_UPDATE = "Обновил пользователя"

    PAY_CREATE = "Оплата создана"
    PAY_UPDATE = "Оплата обновлена"
    PAY_RESIVE = "Оплата получена"
    PAY_CANSEL = "Оплата отменена"

    GAME_SERVER_START = "Сервер запщуен"
    GAME_SERVER_STOP = "Сервер остановлен"

    PLAYER_CREATED = "Игрок создан"
    PLAYER_UPDATE = "Игрок обновлён"
    PLAYER_DELETE = "Игрок удалён"

    SERVICE_CREATE = "Услуга создана"
    SERVICE_UPDATE = "Услуга изменена"
    SERVICE_DELETE = "Услуга удалена"

    LORE_CHAR_CREATE = "Лорный персонаж создан"
    LORE_CHAR_EDIT = "Лорный персонаж изменён"
    LORE_CHAR_DELETE = "Лорный персонаж удалён"


# Реплики с сервера
class UserAccess(Enum):
    NO_ACCESS = 0
    ALL_ACCESS = 1 << 0

    READ_USER = 1 << 1
    CONTROL_USER = 1 << 2

    READ_GAME_SERVER = 1 << 3
    CONTROL_GAME_SERVER = 1 << 4

    READ_PAYMENT = 1 << 5
    GIVE_PAYMENT = 1 << 6
    CONTROL_PAYMENT = 1 << 7

    READ_PLAYER = 1 << 8
    CONTROL_PLAYER = 1 << 9

    READ_LOGS = 1 << 10
    CONTROL_LOGS = 1 << 11

    SERVICE_CONTROL = 1 << 12

    LORE_CHAR_CONTROL = 1 << 13


class LogType(Enum):
    LOGIN = 1
    LOGOUT = 2

    USER_CREATE = 3
    USER_DELETE = 4
    USER_UPDATE = 5

    PAY_CREATE = 6
    PAY_UPDATE = 7
    PAY_RESIVE = 8
    PAY_CANSEL = 9

    GAME_SERVER_START = 10
    GAME_SERVER_STOP = 11

    PLAYER_CREATED = 12
    PLAYER_UPDATE = 13
    PLAYER_DELETE = 14

    SERVICE_CREATE = 15
    SERVICE_UPDATE = 16
    SERVICE_DELETE = 17

    LORE_CHAR_CREATE = 18
    LORE_CHAR_EDIT = 19
    LORE_CHAR_DELETE = 20


class APIManager:
    _base_domain: str = "spf-base.ru"
    _base_url: str = f"https://{_base_domain}/"
    _session: Session = Session()
    cur_user = {
        "login": "",
        "access": 0,
    }

    # region Base
    @classmethod
    def setup(cls) -> None:
        cls._session.headers.update(
            {
                "User-Agent": "spf-agent-v1",
            }
        )

    @classmethod
    def _update_auth_headers(
        cls,
        access_token: str | None = None,
        refresh_token: str | None = None,
        **kwargs,
    ) -> None:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        if refresh_token:
            Config.set_refresh_token_to_file(refresh_token)
            headers["X-Authorization-Refresh"] = f"Bearer {refresh_token}"

        if headers:
            cls._session.headers.update(headers)

    @classmethod
    def _response_sanity_check(cls, response: Response) -> Any:
        if not response.ok:
            try:
                error_detail = response.json().get("detail", response.text)

            except Exception:
                error_detail = response.text

            raise APIError(error_detail, response.status_code)

        try:
            return response.json()

        except Exception:
            raise ValueError("Response does not contain json")

    @classmethod
    def _requests(
        cls,
        method: Literal["GET", "POST"],
        url: str,
        _retry: bool = True,
        **kwargs,
    ):
        try:
            response = cls._session.request(method, cls._base_url + url, **kwargs)
            return cls._response_sanity_check(response)

        except APIError as err:
            if str(err) == "Token expired":
                if _retry:
                    cls._refresh()
                    return cls._requests(method, url, False, **kwargs)

                else:
                    sys.exit(1)

            else:
                raise err

    @classmethod
    def _refresh(cls) -> None:
        response = cls._session.get(cls._base_url + "api/auth/refresh")
        json_data = cls._response_sanity_check(response)

        cls._update_auth_headers(**json_data)

    # endregion

    # region etc
    @classmethod
    def has_access(cls, value: int) -> bool:
        if (
            cls.cur_user["access"] & UserAccess.ALL_ACCESS.value
        ) == UserAccess.ALL_ACCESS.value:
            return True

        return (cls.cur_user["access"] & value) == value

    @classmethod
    def update_cur_user(cls) -> None:
        json_data = cls._requests("GET", "/api/user_control/me")
        cls.cur_user["login"] = json_data["login"]
        cls.cur_user["access"] = json_data["access"]

    # endregion

    class download:
        @classmethod
        def version(cls) -> str | None:
            try:
                json_data = APIManager._requests("GET", "download/version")
                return json_data.get("version", None)

            except Exception:
                return None

    class auth:
        @classmethod
        def login(cls, login: str, password: str) -> None:
            json_data = APIManager._requests(
                "POST",
                "api/auth/login",
                json={
                    "username": login,
                    "password": password,
                },
            )

            APIManager._update_auth_headers(**json_data)
            WebSocketClient.connect(
                f"wss://{APIManager._base_domain}/api/websocket/connect",
                APIManager._session.headers["Authorization"],  # type: ignore
            )

        @classmethod
        def register(cls, login: str, password: str) -> None:
            json_data = APIManager._requests(
                "POST",
                "api/auth/register",
                json={
                    "username": login,
                    "password": password,
                },
            )

            APIManager._update_auth_headers(**json_data)
            WebSocketClient.connect(
                f"wss://{APIManager._base_domain}/api/websocket/connect",
                APIManager._session.headers["Authorization"],  # type: ignore
            )

        @classmethod
        def login_refresh(cls) -> bool:
            try:
                APIManager._update_auth_headers(
                    refresh_token=Config.get_refresh_token_form_file()
                )
                APIManager._refresh()
                WebSocketClient.connect(
                    f"wss://{APIManager._base_domain}/api/websocket/connect",
                    APIManager._session.headers["Authorization"],  # type: ignore
                )
                return True

            except Exception:
                return False

        @classmethod
        def logout(cls) -> None:
            Config.set_refresh_token_to_file("")
            cls.cur_user = {
                "login": "",
                "access": 0,
            }

    class user_control:
        @classmethod
        def get_info(cls, target: str) -> dict:
            return APIManager._requests(
                "POST",
                "/api/user_control/get_info",
                json={"target": target},
            )

        @classmethod
        def get_all(cls) -> list:
            return APIManager._requests("GET", "/api/user_control/get_all").get(
                "logins", []
            )

        @classmethod
        def delete(cls, target: str) -> None:
            APIManager._requests(
                "POST", "/api/user_control/delete", json={"target": target}
            )

        @classmethod
        def set_access(cls, target: str, access: int) -> None:
            APIManager._requests(
                "POST",
                "/api/user_control/set_access",
                json={"target": target, "access": access},
            )

    class server_control:
        @classmethod
        def start(cls) -> None:
            APIManager._requests("GET", "/api/server_control/start")

        @classmethod
        def stop(cls) -> None:
            APIManager._requests("GET", "/api/server_control/stop")

        @classmethod
        def status(cls) -> str:
            return APIManager._requests("GET", "/api/server_control/status").get(
                "status"
            )

        @classmethod
        def status_subscribe(cls) -> dict[str, str]:
            return APIManager._requests("GET", "/api/server_control/status/subscribe")

        @classmethod
        def status_unsubscribe(cls) -> dict[str, str]:
            return APIManager._requests("GET", "/api/server_control/status/unsubscribe")

    class player_control:
        @classmethod
        def create(cls, discord_name: str, steam_url: str) -> None:
            APIManager._requests(
                "POST",
                "/api/player_control/create",
                json={
                    "discord_name": discord_name,
                    "steam_url": steam_url,
                },
            )

        @classmethod
        def get(
            cls,
            discord_id: str | None = None,
            steam_id: str | None = None,
        ) -> list[dict]:
            query_str = ""
            if bool(discord_id or steam_id):
                query_str = "?"
                if discord_id:
                    query_str += f"discord_id={discord_id}"
                if steam_id:
                    if query_str != "?":
                        query_str += "&"
                    query_str += f"steam_id={steam_id}"

            return APIManager._requests("GET", f"/api/player_control/get{query_str}")

        @classmethod
        def edit(
            cls,
            u_id: int,
            discord_name: str | None,
            blacklist: dict[str, bool] | None,
            mb_limit: float | None,
            mb_taken: float | None,
        ) -> None:
            APIManager._requests(
                "POST",
                "/api/player_control/edit",
                json={
                    "u_id": u_id,
                    "discord_name": discord_name,
                    "blacklist": blacklist,
                    "mb_limit": mb_limit,
                    "mb_taken": mb_taken,
                },
            )

        @classmethod
        def add_note(cls, u_id: int, text: str) -> None:
            APIManager._requests(
                "POST",
                "/api/player_control/note/add",
                json={
                    "u_id": u_id,
                    "text": text,
                },
            )

        @classmethod
        def change_note_status(cls, u_id: int, index: int, status: str) -> None:
            APIManager._requests(
                "POST",
                "/api/player_control/note/status",
                json={
                    "u_id": u_id,
                    "index": index,
                    "status": status,
                },
            )

    class lore_char_control:
        @classmethod
        def get(cls) -> dict[str, Any]:
            return APIManager._requests("GET", "/api/lore_char_control/get")

        @classmethod
        def create(
            cls,
            key: str,
            name: str,
            status: Literal["free", "taken", "blocked"],
            wiki: str | None,
        ) -> None:
            APIManager._requests(
                "POST",
                "/api/lore_char_control/create",
                json={
                    "key": key,
                    "name": name,
                    "status": status,
                    "wiki": wiki,
                },
            )

        @classmethod
        def edit(
            cls,
            key: str,
            name: str,
            status: Literal["free", "taken", "blocked"],
            wiki: str | None,
        ) -> None:
            APIManager._requests(
                "POST",
                "/api/lore_char_control/edit",
                json={
                    "key": key,
                    "name": name,
                    "status": status,
                    "wiki": wiki,
                },
            )

        @classmethod
        def delete(cls, key: str) -> None:
            APIManager._requests(
                "POST",
                "/api/lore_char_control/delete",
                json={"key": key},
            )

    class logs:
        @classmethod
        def by_creator(cls, creator: str) -> list[dict[str, Any]]:
            return APIManager._requests(
                "POST", "/api/logs/by_creator", json={"target": creator}
            )

        @classmethod
        def by_range(cls, start_id: int, end_id: int) -> list[dict[str, Any]]:
            return APIManager._requests(
                "POST",
                "/api/logs/by_range",
                json={"start_id": start_id, "end_id": end_id},
            )

        @classmethod
        def by_time_range(
            cls,
            start_time: datetime,
            end_time: datetime,
        ) -> list[dict[str, Any]]:
            return APIManager._requests(
                "POST",
                "/api/logs/by_time_range",
                json={"start_time": start_time, "end_time": end_time},
            )

        @classmethod
        def min_max_id(cls) -> dict[str, int]:
            return APIManager._requests("GET", "/api/logs/min_max_id")

    class service_control:
        @classmethod
        def create(
            cls,
            name: str,
            description: str,
            price_main: str,
            discount_value: int = 0,
            discount_date: str | None = None,
            status: Literal["on", "off", "archive"] = "off",
            left: int | None = None,
            sell_time: str | None = None,
            oferta_limit: bool = False,
        ) -> dict:
            return APIManager._requests(
                "POST",
                "/api/service_control/create",
                json={
                    "name": name,
                    "description": description,
                    "price_main": price_main,
                    "discount_value": discount_value,
                    "discount_date": discount_date,
                    "status": status,
                    "left": left,
                    "sell_time": sell_time,
                    "oferta_limit": oferta_limit,
                },
            )

        @classmethod
        def delete(cls, u_id: str) -> dict:
            return APIManager._requests(
                "POST",
                "/api/service_control/delete",
                json={"u_id": u_id},
            )

        @classmethod
        def edit(cls, u_id: str, **fields) -> dict:
            payload = {"u_id": u_id}
            payload.update(fields)

            return APIManager._requests(
                "POST",
                "/api/service_control/edit",
                json=payload,
            )

        @classmethod
        def get(cls, u_id: str) -> dict:
            return APIManager._requests(
                "POST",
                "/api/service_control/get",
                json={"u_id": str(u_id)},
            )

        @classmethod
        def list(cls) -> list[dict]:
            return APIManager._requests("GET", "/api/service_control/list")

    class payment_control:
        @classmethod
        def create(
            cls,
            player_id: str,
            items: list[dict],
            commission_key: str = "AC",
            status: str = "pending",
        ) -> dict:
            return APIManager._requests(
                "POST",
                "/api/payment_control/create",
                json={
                    "player_id": player_id,
                    "items": items,
                    "commission_key": commission_key,
                    "status": status,
                },
            )

        @classmethod
        def delete(cls, u_id: str) -> dict:
            return APIManager._requests(
                "POST",
                "/api/payment_control/delete",
                json={"u_id": u_id},
            )

        @classmethod
        def edit(
            cls,
            u_id: str,
            status: str | None = None,
            player_id: str | None = None,
            commission_key: str | None = None,
        ) -> dict:
            payload: dict = {"u_id": u_id}
            if status is not None:
                payload["status"] = status
            if player_id is not None:
                payload["player_id"] = player_id
            if commission_key is not None:
                payload["commission_key"] = commission_key

            return APIManager._requests(
                "POST",
                "/api/payment_control/edit",
                json=payload,
            )

        @classmethod
        def get(cls, u_id: str) -> dict:
            return APIManager._requests(
                "POST",
                "/api/payment_control/get",
                json={"u_id": u_id},
            )

        @classmethod
        def list(cls) -> list[dict]:
            return APIManager._requests("GET", "/api/payment_control/list")
