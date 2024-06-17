"""The E-Redes Balcao Digital Readings integration hub."""

from homeassistant.core import HomeAssistant

from .captcha import ERedesCaptchaSolver
from .exceptions import InvalidAuth


class ERedesHub:
    """E-Redes Hub."""

    def __init__(
        self,
        hass: HomeAssistant,
        captcha_api_key: str,
        captcha_api_endpoint: str,
        user_nif: str,
        password: str,
        home_cpe: str,
    ) -> None:
        """Initialize."""

        self.hass = hass
        self.captcha_api_key = captcha_api_key
        self.captcha_api_endpoint = captcha_api_endpoint
        self.user_nif = user_nif
        self.password = password
        self.home_cpe = home_cpe

        self.captcha_solver = ERedesCaptchaSolver(
            self.captcha_api_key, self.captcha_api_endpoint, self.hass
        )

    async def is_captcha_api_key_valid(self) -> bool:
        """Check if captcha API key is valid."""

        try:
            await self.captcha_solver.get_credits()
        except InvalidAuth:
            return False
        else:
            return True

    async def get_captcha_solver_credits(self) -> float:
        """Get 2captcha balance."""

        return await self.captcha_solver.get_credits()
