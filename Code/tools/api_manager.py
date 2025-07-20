import logging
from typing import Final

from requests import Response, Session

logger = logging.getLogger(__name__)


class APIManager:
    _base_url: Final[str] = "https://spf-base.ru/"
    _session: Session = Session()

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
        access_token: str | None,
        refresh_token: str | None,
        **kwargs,
    ) -> None:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        if refresh_token:
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

    # region base_url/auth
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
        logger.info("Token expired, refreshing...")
        response = cls._session.post(
            cls._base_url + "api/auth/refresh",
        )
        # Нельзя использовать requests_post, иначе будет бесконечная рекурсия 100%
        json_data = cls._response_sanity_check(response)

        cls._update_headers(**json_data)

    # endregion
