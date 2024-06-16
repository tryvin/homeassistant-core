"""E-Redes Balcao Digital Readings Captcha Balance Sensors."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify

from ... import CannotConnect, ERedesHub, InvalidAuth, const


class CaptchaBalanceSensor(SensorEntity):
    """Captcha balance sensor."""

    _attr_name = "Captcha Balance"
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, device_info: DeviceInfo, user_cpe: str, key_masked: str) -> None:
        """Initialize device."""

        self._attr_device_info = device_info
        self._attr_unique_id = slugify(f"captcha_balance_{user_cpe}")
        self._attr_icon = "mdi:currency-usd"
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self.user_cpe = user_cpe
        self._attr_extra_state_attributes = {
            "user_cpe": user_cpe,
            "key_masked": key_masked,
        }

    async def async_update(self):
        """Update the captcha balance."""

        if self.user_cpe in self.hass.data[const.DOMAIN]:
            e_redes_hub: ERedesHub = self.hass.data[const.DOMAIN][self.user_cpe]

            try:
                self._attr_native_value = await e_redes_hub.get_captcha_solver_credits()
            except (InvalidAuth, CannotConnect):
                self._attr_native_value = None
        else:
            self._attr_native_value = None
