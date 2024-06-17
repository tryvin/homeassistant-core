"""The E-Redes Balcao Digital Readings integration captcha solver."""

from asyncio import sleep as asyncio_sleep
from random import randint
from typing import Final

from aiohttp.client import ClientResponse

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..const import DEFAULT_TIMEOUT, USER_AGENT
from .exceptions import CannotConnect, CaptchaFailedToSolve, InvalidAuth

E_REDES_SITE_KEY: Final = "6LdpTzceAAAAALzJon5hGYboD6hiYxJqd1-Lpxyi"
E_REDES_PAGE_ACTION: Final = "AuthRecaptchaInterceptor"
E_REDES_MIN_SCORE: Final = 0.7
E_REDES_CONSUMPTIONS_HISTORY: Final = (
    "https://balcaodigital.e-redes.pt/consumptions/history"
)


class ERedesCaptchaSolver:
    """E redes captcha solver."""

    def __init__(self, api_key: str, api_base_url: str, hass: HomeAssistant) -> None:
        """Initialize."""

        self.api_key = api_key
        self.api_base_url = api_base_url
        self.hass = hass

    async def __call_api(self, endpoint, json_data=None) -> ClientResponse:
        return await async_create_clientsession(self.hass).post(
            f"{self.api_base_url}/{endpoint}",
            json={"clientKey": self.api_key} | (json_data or {}),
            timeout=DEFAULT_TIMEOUT.total_seconds(),
        )

    def __handle_api_error(self, status_code, response_data):
        if status_code in (200, 400, 401):
            if "errorCode" in response_data:
                if str(response_data["errorCode"]).startswith("ERROR_KEY_"):
                    raise InvalidAuth

        raise CannotConnect

    async def get_credits(self) -> float:
        """Get the balance for the account."""

        try:
            credits_response = await self.__call_api(
                endpoint="getBalance",
            )
        except Exception as e:
            raise CannotConnect from e

        if credits_response.status == 200:
            credits_data = await credits_response.json()

            if "errorId" in credits_data and credits_data["errorId"] == 1:
                return self.__handle_api_error(credits_response.status, credits_data)

            if "balance" in credits_data:
                return float(credits_data["balance"])
        elif credits_response.status in (400, 401):
            credits_data = await credits_response.json()

            self.__handle_api_error(credits_response.status, credits_data)

        raise CannotConnect

    async def retrieve_captcha(self, for_url: str) -> list[str]:
        """Retrieve captcha for URL."""

        try:
            create_task_response = await self.__call_api(
                endpoint="createTask",
                json_data={
                    "task": {
                        "type": "RecaptchaV3TaskProxyless",
                        "websiteURL": for_url,
                        "websiteKey": E_REDES_SITE_KEY,
                        "pageAction": E_REDES_PAGE_ACTION,
                        "minScore": E_REDES_MIN_SCORE,
                        "userAgent": USER_AGENT,
                    }
                },
            )
        except Exception as e:
            raise CannotConnect from e

        captcha_id = None

        if create_task_response.status == 200:
            create_task_data = await create_task_response.json()

            if "errorId" in create_task_data and create_task_data["errorId"] == 1:
                return self.__handle_api_error(
                    create_task_response.status, create_task_data
                )

            if "taskId" in create_task_data:
                captcha_id = create_task_data["taskId"]
        elif create_task_response.status in (400, 401):
            create_task_data = await create_task_response.json()

            return self.__handle_api_error(
                create_task_response.status, create_task_data
            )

        if not captcha_id:
            raise CannotConnect

        current_request_count = 0
        while current_request_count < 120:
            try:
                fetch_task_response = await self.__call_api(
                    endpoint="getTaskResult",
                    json_data={"taskId": captcha_id},
                )

                if fetch_task_response.status == 200:
                    fetch_task_data = await fetch_task_response.json()

                    if (
                        "status" in fetch_task_data
                        and fetch_task_data["status"] == "ready"
                    ):
                        return [
                            fetch_task_data["solution"]["gRecaptchaResponse"],
                            captcha_id,
                        ]
            except Exception:  # noqa: BLE001
                pass
            finally:
                current_request_count += 1

            await asyncio_sleep(randint(2, 10))

        raise CaptchaFailedToSolve

    async def report_captcha(self, captcha_id: str, is_valid: bool = True) -> None:
        """Report captcha was valid or invalid."""

        try:
            await self.__call_api(
                endpoint="reportCorrectRecaptcha"
                if is_valid
                else "reportIncorrectRecaptcha",
                json_data={"taskId": captcha_id},
            )
        except Exception as e:
            raise CannotConnect from e
