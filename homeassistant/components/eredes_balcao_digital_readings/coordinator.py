"""E-redes data fetching coordinator."""

from asyncio import timeout as async_timeout
from datetime import UTC, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .config_flow import _LOGGER
from .core.exceptions import (
    CaptchaFailedToConnectToApi,
    CaptchaFailedToSolve,
    InvalidAuth,
)
from .core.hub import ERedesHub
from .core.site_scrapper import SiteScrapper


class ERedesDataCoordinator(DataUpdateCoordinator[dict]):
    """E-Redes data fetching coordinator."""

    def __init__(self, hass: HomeAssistant, hub: ERedesHub) -> None:
        """Initialize data."""

        super().__init__(
            hass,
            _LOGGER,
            name="E-Redes Readings",
            update_interval=timedelta(days=1),
        )

        self.hub = hub
        self.site_scrapper = SiteScrapper(
            hass,
            self.hub.captcha_solver,
            self.hub.user_nif,
            self.hub.password,
            self.hub.home_cpe,
        )

        self.end_day = 1

    async def _async_update_data(self):
        try:
            php_session = await self.site_scrapper.fetch_php_session()

            user_token = await self.site_scrapper.fetch_user_token(
                php_session=php_session
            )

            try_count = 0
            last_except = None

            while try_count < 3:
                async with async_timeout(90):
                    try:
                        current_time = datetime.now()

                        return await self.site_scrapper.fetch_formatted_readings_for_period(
                            current_time.replace(
                                day=1, hour=0, minute=0, second=0, tzinfo=UTC
                            ),
                            current_time.replace(
                                hour=23,
                                minute=59,
                                second=59,
                                tzinfo=UTC,
                            ),
                            user_token["php_session"],
                            user_token["jwt_token"],
                        )

                    except (CaptchaFailedToConnectToApi, CaptchaFailedToSolve) as e:
                        last_except = e
                        try_count += 1

            raise last_except
        except InvalidAuth as e:
            raise ConfigEntryAuthFailed from e
        except Exception as e:
            raise UpdateFailed(f"Error communicating with API: {e}") from e
