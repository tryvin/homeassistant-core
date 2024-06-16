"""E-redes site connector."""

from datetime import UTC, datetime, timedelta
from typing import Final

from aiohttp.client import ClientResponse
import jwt

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..config_flow import _LOGGER
from ..const import DEFAULT_TIMEOUT
from .captcha import ERedesCaptchaSolver
from .exceptions import (
    CannotConnect,
    CaptchaFailedToConnectToApi,
    CaptchaFailedToSolve,
    InvalidAuth,
)

USER_AGENT: Final = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
HOME_URL: Final = "https://balcaodigital.e-redes.pt/"
ORIGIN_URL: Final = "https://balcaodigital.e-redes.pt"
DEFAULT_HEADERS: Final = {
    "User-Agent": USER_AGENT,
}


class SiteScrapper:
    """Site scrapper."""

    def __init__(
        self,
        hass: HomeAssistant,
        captcha_solver: ERedesCaptchaSolver,
        user_nif: str,
        password: str,
        home_cpe: str,
    ) -> None:
        """Initialize."""

        self.hass = hass
        self.captcha_solver = captcha_solver
        self.user_nif = user_nif
        self.password = password
        self.home_cpe = home_cpe

    async def __fetch_url(self, url) -> ClientResponse:
        return await async_create_clientsession(self.hass).get(
            url, timeout=DEFAULT_TIMEOUT.total_seconds(), headers=DEFAULT_HEADERS
        )

    async def __post_json_url(
        self,
        url,
        php_session,
        json_data,
        extra_headers=None,
        referer=ORIGIN_URL,
        extra_cookies=None,
    ) -> ClientResponse:
        return await async_create_clientsession(self.hass).post(
            url,
            json=json_data,
            timeout=DEFAULT_TIMEOUT.total_seconds(),
            cookies={"PHPSESSID": php_session}
            | (extra_cookies if extra_cookies is not None else {}),
            headers=DEFAULT_HEADERS
            | (extra_headers if extra_headers is not None else {})
            | {"origin": ORIGIN_URL, "referer": referer},
        )

    async def fetch_php_session(self) -> str | None:
        """Fetch the PHP session cookie."""

        _LOGGER.debug("Requesting PHPsessid")

        home_response = await self.__fetch_url(HOME_URL)

        if home_response.status == 200:
            for k, v in home_response.cookies.items():
                if k == "PHPSESSID":
                    return v.value

        _LOGGER.debug("PHP session not found: %s", home_response.cookies)

        return None

    async def fetch_user_token(self, php_session: str | None = None) -> dict | None:
        """Fetch the authenticated user token."""

        if php_session is None:
            php_session = await self.fetch_php_session()

        _LOGGER.debug("PHP session: %s", php_session)

        if php_session is None:
            raise CaptchaFailedToConnectToApi

        try:
            # First Fetch a Captcha for the Login Page
            _LOGGER.debug("Requesting captcha for login endpoint")
            [captcha_token, captcha_id] = await self.captcha_solver.retrieve_captcha(
                "https://balcaodigital.e-redes.pt/login"
            )

            _LOGGER.debug(
                "Captcha Token: %s, Captcha ID: %s", captcha_token, captcha_id
            )
        except Exception as e:
            _LOGGER.error("Failed to catcha: %s", e)

            raise CaptchaFailedToConnectToApi from e

        _LOGGER.debug("Requesting login endpoint")
        signin_response = await self.__post_json_url(
            url=ORIGIN_URL + "/ms/auth/auth/signin",
            php_session=php_session,
            json_data={"username": self.user_nif, "password": self.password},
            extra_headers={"authorization-request": captcha_token},
            referer=ORIGIN_URL + "/login?returnUrl=%2Freadings%2Fhistory",
        )

        aat_cookie = None

        _LOGGER.debug(
            "Login response: %s, %s",
            signin_response.status,
            await signin_response.text(),
        )

        if signin_response.status == 200:
            for k, v in signin_response.cookies.items():
                if k == "aat":
                    aat_cookie = v.value

            await self.captcha_solver.report_captcha(captcha_id, True)

            response_body = await signin_response.json()

            if "Body" in response_body and not response_body["Body"]["Success"]:
                raise InvalidAuth

        elif signin_response.status in (401, 403):
            await self.captcha_solver.report_captcha(captcha_id, False)

            raise CaptchaFailedToSolve

        if not aat_cookie:
            raise CannotConnect

        try:
            # Second Fetch a Captcha for the Session Endpoint
            _LOGGER.debug("Requesting captcha for session endpoint")
            [captcha_token, captcha_id] = await self.captcha_solver.retrieve_captcha(
                "https://balcaodigital.e-redes.pt/login"
            )

            _LOGGER.debug(
                "Captcha Token: %s, Captcha ID: %s", captcha_token, captcha_id
            )
        except Exception as e:
            _LOGGER.error("Failed to catcha: %s", e)

            raise CaptchaFailedToConnectToApi from e

        _LOGGER.debug("Requesting session endpoint")
        session_response = await self.__post_json_url(
            url=ORIGIN_URL + "/session",
            php_session=php_session,
            json_data={"username": self.user_nif, "password": self.password},
            extra_headers={"authorization-request": captcha_token},
            referer=ORIGIN_URL + "/login?returnUrl=%2Freadings%2Fhistory",
            extra_cookies={"aat": aat_cookie},
        )

        _LOGGER.debug(
            "Session response: %s, %s",
            session_response.status,
            await session_response.text(),
        )

        if session_response.status == 200:
            await self.captcha_solver.report_captcha(captcha_id, True)

            decoded_jwt = jwt.decode(aat_cookie, options={"verify_signature": False})

            return {
                "php_session": php_session,
                "jwt_token": aat_cookie,
                "expires_at": datetime.fromtimestamp(decoded_jwt["exp"], tz=UTC)
                if "exp" in decoded_jwt
                else datetime.now(tz=UTC) + timedelta(hours=2),
            }

        if session_response.status in (401, 403):
            await self.captcha_solver.report_captcha(captcha_id, False)

            raise CaptchaFailedToSolve

        raise CannotConnect

    def __parse_formatted_readings(
        self, readings_data: dict, end_date: datetime
    ) -> dict:
        data_formatted: dict = {"ponta": {}, "cheia": {}, "vazia": {}}

        for equipments_info in readings_data["Body"]["Result"]:
            if (
                "Readings" in equipments_info
                and "active" in equipments_info["Readings"]
            ):
                for reading_info in equipments_info["Readings"]["active"]:
                    day_date = datetime.strptime(
                        reading_info["date"], "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=UTC)

                    if day_date <= end_date:
                        if "C" in reading_info:
                            data_formatted["cheia"][reading_info["date"]] = (
                                reading_info["C"]
                            )

                        if "P" in reading_info:
                            data_formatted["ponta"][reading_info["date"]] = (
                                reading_info["P"]
                            )

                        if "V" in reading_info:
                            data_formatted["vazia"][reading_info["date"]] = (
                                reading_info["V"]
                            )

        return data_formatted

    async def fetch_formatted_readings_for_period(
        self, start_date: datetime, end_date: datetime, php_session: str, jwt_token: str
    ) -> dict:
        """Fetch daily readings formatted."""

        try:
            # Fetch a Captcha for the Session Endpoint
            _LOGGER.debug("Requesting captcha for readings endpoint")
            [captcha_token, captcha_id] = await self.captcha_solver.retrieve_captcha(
                ORIGIN_URL + "/readings/history"
            )

            _LOGGER.debug(
                "Captcha Token: %s, Captcha ID: %s", captcha_token, captcha_id
            )
        except Exception as e:
            _LOGGER.error("Failed to catcha: %s", e)

            raise CaptchaFailedToConnectToApi from e

        _LOGGER.debug("Requesting readings")

        readings_response = await self.__post_json_url(
            url=ORIGIN_URL + "/ms/reading/data-usage/edm/get",
            php_session=php_session,
            json_data={
                "cpe": self.home_cpe,
                "request_type": "1",
                "start_date": start_date.strftime("%Y-%m-%d 00:00:00"),
                "end_date": end_date.strftime("%Y-%m-%d 23:59:59"),
                "wait": True,
                "formatted": True,
                "nif_requester": None,
                "nif": None,
            },
            extra_headers={"authorization-request": captcha_token},
            referer=ORIGIN_URL + "/readings/history",
            extra_cookies={"aat": jwt_token},
        )

        _LOGGER.debug(
            "Readings response: %s, %s",
            readings_response.status,
            await readings_response.text(),
        )

        data_formatted: dict = {"ponta": {}, "cheia": {}, "vazia": {}}

        if readings_response.status == 200:
            await self.captcha_solver.report_captcha(captcha_id, True)

            readings_data = await readings_response.json()

            _LOGGER.debug("Readings response json: %s", readings_data)

            if "Body" in readings_data and readings_data["Body"]["Success"]:
                data_formatted = self.__parse_formatted_readings(
                    readings_data, end_date
                )

        elif readings_response.status in (401, 403):
            await self.captcha_solver.report_captcha(captcha_id, False)

            raise CaptchaFailedToSolve

        return data_formatted
