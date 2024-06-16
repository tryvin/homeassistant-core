"""The E-Redes Balcao Digital Readings integration captcha solver."""

from typing import Final

from twocaptcha import TwoCaptcha

from homeassistant.core import HomeAssistant

from .exceptions import CannotConnect, InvalidAuth

E_REDES_SITE_KEY: Final = "6LdpTzceAAAAALzJon5hGYboD6hiYxJqd1-Lpxyi"
E_REDES_PAGE_ACTION: Final = "AuthRecaptchaInterceptor"
E_REDES_MIN_SCORE: Final = "0.7"
E_REDES_CONSUMPTIONS_HISTORY: Final = (
    "https://balcaodigital.e-redes.pt/consumptions/history"
)


class ERedesCaptchaSolver:
    """E redes captcha solver."""

    def __init__(self, api_key: str, hass: HomeAssistant) -> None:
        """Initialize."""

        self.api_key = api_key
        self.solver = TwoCaptcha(apiKey=self.api_key)
        self.hass = hass

    async def get_credits(self) -> float:
        """Get the balance for the account."""

        try:
            api_result = await self.hass.async_add_executor_job(
                lambda: self.solver.api_client.res(
                    key=self.api_key, action="getbalance"
                )
            )
        except Exception as e:
            if str(e) == "ERROR_WRONG_USER_KEY":
                raise InvalidAuth from e

            raise CannotConnect from e

        if api_result == "ERROR_KEY_DOES_NOT_EXIST":
            raise InvalidAuth

        return float(api_result)

    async def retrieve_captcha(self, for_url: str) -> list[str]:
        """Retrieve captcha for URL."""

        try:
            api_result = await self.hass.async_add_executor_job(
                lambda: self.solver.recaptcha(
                    sitekey=E_REDES_SITE_KEY,
                    url=for_url,
                    version="v3",
                    action=E_REDES_PAGE_ACTION,
                    score=E_REDES_MIN_SCORE,
                )
            )

            return [
                api_result["code"],
                api_result["captchaId"],
            ]
        except Exception as e:
            raise CannotConnect from e

    async def report_captcha(self, captcha_id: str, is_valid: bool = True) -> None:
        """Report captcha was valid or invalid."""

        try:
            await self.hass.async_add_executor_job(
                lambda: self.solver.report(captcha_id, is_valid)
            )
        except Exception as e:
            raise CannotConnect from e
