"""E-Redes Balcao Digital Readings Captcha Balance Sensors."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from ...coordinator import ERedesDataCoordinator


class EnergyAccumulatorBalance(CoordinatorEntity, SensorEntity):
    """Energy accumulator balance sensor."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        device_info: DeviceInfo,
        user_cpe: str,
        key_masked: str,
        coordinator: ERedesDataCoordinator,
        coordinator_key: str,
    ) -> None:
        """Initialize device."""

        super().__init__(coordinator, coordinator_key)

        self.coordinator = coordinator
        self._attr_name = f"Energy Accumulator {coordinator_key}"

        self._attr_device_info = device_info
        self._attr_unique_id = slugify(
            f"energy_accumulator_{user_cpe}_{coordinator_key}"
        )
        self._attr_icon = "mdi:lightning-bolt"
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self.user_cpe = user_cpe
        self._attr_extra_state_attributes = {
            "user_cpe": user_cpe,
            "key_masked": key_masked,
            "coordinator_key": coordinator_key,
        }

        self.idx = coordinator_key

    @callback
    async def async_added_to_hass(self) -> None:
        """Handle it being added to home assistant."""

        await super().async_added_to_hass()

        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self.coordinator.data and len(self.coordinator.data[self.idx]) > 0:
            self._attr_native_value = self.coordinator.data[self.idx][
                max(self.coordinator.data[self.idx])
            ]
        else:
            self._attr_native_value = None

        self.async_write_ha_state()
