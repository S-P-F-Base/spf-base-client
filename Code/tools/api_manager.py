import logging
from enum import Enum
from typing import Final

from requests import Response, Session

from .config import Config

logger = logging.getLogger(__name__)


# Реплика с сервера
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


class APIManager:
    _base_url: Final[str] = "https://spf-base.ru/"
    _session: Session = Session()

    cur_user = {
        "login": "",
        "access": 0,
    }

    @classmethod
    def setup(cls) -> None:
        cls._session.headers.update(
            {
                "User-Agent": "spf-agent-v1",
            }
        )

    @classmethod
    def _update_headers(
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

            raise ValueError(error_detail)

        try:
            return response.json()

        except Exception:
            raise ValueError("Response does not contain json")

    # region requests
    @classmethod
    def requests_get(
        cls,
        url: str,
        params: dict | None = None,
        _retry: bool = True,
    ) -> dict:
        try:
            response = cls._session.get(cls._base_url + url, params=params or {})
            return cls._response_sanity_check(response)

        except ValueError as err:
            if str(err) == "Token expired" and _retry:
                cls.auth_refresh()
                return cls.requests_get(url, params, False)

            else:
                raise err

    @classmethod
    def requests_post(
        cls,
        url: str,
        json: dict | None,
        _retry: bool = True,
    ) -> dict:
        try:
            response = cls._session.post(cls._base_url + url, json=json)
            return cls._response_sanity_check(response)

        except ValueError as err:
            if str(err) == "Token expired" and _retry:
                cls.auth_refresh()
                return cls.requests_post(url, json, False)

            else:
                raise err

    # endregion

    # region base_url/download
    @classmethod
    def download_version(cls) -> str | None:
        try:
            response = cls._session.get(cls._base_url + "download/version")
            return response.json().get("version") if response.ok else None

        except Exception:
            return None

    # endregion

    # region base_url/api/auth
    @classmethod
    def auth_login(cls, login: str, password: str) -> None:
        json_data = cls.requests_post(
            "api/auth/login",
            {
                "username": login,
                "password": password,
            },
        )

        cls._update_headers(**json_data)

    @classmethod
    def auth_register(cls, login: str, password: str) -> None:
        json_data = cls.requests_post(
            "api/auth/register",
            {
                "username": login,
                "password": password,
            },
        )
        cls._update_headers(**json_data)

    @classmethod
    def auth_refresh(cls) -> None:
        response = cls._session.post(
            cls._base_url + "api/auth/refresh",
        )
        # Нельзя использовать requests_post, иначе будет бесконечная рекурсия 100%
        json_data = cls._response_sanity_check(response)

        cls._update_headers(**json_data)

    @classmethod
    def try_auth_viva_refresh(cls) -> bool:
        try:
            cls._update_headers(refresh_token=Config.get_refresh_token_form_file())
            cls.auth_refresh()
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

    # endregion

    # region base_url/api/user_control
    @classmethod
    def user_control_get_info(cls, target: str) -> dict:
        json_data = cls.requests_post(
            "/api/user_control/get_info",
            json={"target": target},
        )

        return json_data

    @classmethod
    def user_control_get_all(cls) -> list:
        json_data = cls.requests_get("/api/user_control/get_all")
        return json_data.get("logins", [])

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
        json_data = cls.requests_get("/api/user_control/me")
        cls.cur_user["login"] = json_data["login"]
        cls.cur_user["access"] = json_data["access"]

    # endregion
