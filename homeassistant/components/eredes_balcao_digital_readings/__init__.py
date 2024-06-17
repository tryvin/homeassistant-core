"""The E-Redes Balcao Digital Readings integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_KEY,
    CONF_CAPTCHA_API_ENDPOINT,
    CONF_CPE,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from .coordinator import ERedesDataCoordinator
from .core.exceptions import CannotConnect, InvalidAuth  # noqa: F401
from .core.hub import ERedesHub

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up E-Redes Balcao Digital Readings from a config entry."""

    eredes_hub = ERedesHub(
        hass,
        captcha_api_key=entry.data[CONF_API_KEY],
        captcha_api_endpoint=entry.data[CONF_CAPTCHA_API_ENDPOINT],
        user_nif=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        home_cpe=entry.data[CONF_CPE],
    )
    coordinator = ERedesDataCoordinator(hass, eredes_hub)

    entry.runtime_data = {"hub": eredes_hub, "coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# https://balcaodigital.e-redes.pt/favicon.ico
