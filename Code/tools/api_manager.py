import logging
from enum import Enum
from typing import Final, Literal

from requests import Response, Session

from .config import Config

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


# Реплика с сервераы
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


class APIManager:
    _base_url: Final[str] = "https://spf-base.ru/"
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
    def _response_sanity_check(cls, response: Response) -> dict:
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
            if str(err) == "Token expired" and _retry:
                cls._refresh()
                return cls._requests(method, url, False, **kwargs)

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

        @classmethod
        def login_refresh(cls) -> bool:
            try:
                APIManager._update_auth_headers(
                    refresh_token=Config.get_refresh_token_form_file()
                )
                APIManager._refresh()
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
            json_data = APIManager._requests(
                "POST",
                "/api/user_control/get_info",
                json={"target": target},
            )

            return json_data

        @classmethod
        def get_all(cls) -> list:
            json_data = APIManager._requests("GET", "/api/user_control/get_all")
            return json_data.get("logins", [])
