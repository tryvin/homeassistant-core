"""Config flow for E-Redes Balcao Digital Readings integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow as BaseConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import (
    _LOGGER,
    CONF_API_KEY,
    CONF_CAPTCHA_API_ENDPOINT,
    CONF_CPE,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)
from .core.exceptions import CannotConnect, InvalidAuth
from .core.hub import ERedesHub

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_CAPTCHA_API_ENDPOINT): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CPE): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = ERedesHub(
        hass,
        captcha_api_key=data[CONF_API_KEY],
        captcha_api_endpoint=data[CONF_CAPTCHA_API_ENDPOINT],
        user_nif=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        home_cpe=data[CONF_CPE],
    )

    if not await hub.is_captcha_api_key_valid():
        raise InvalidAuth

    return {"title": "E-Redes CPE: " + data[CONF_CPE]}


class ConfigFlow(BaseConfigFlow, domain=DOMAIN):
    """Handle a config flow for E-Redes Balcao Digital Readings."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
