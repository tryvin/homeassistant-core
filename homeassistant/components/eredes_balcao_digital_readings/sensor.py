"""E-Redes Balcao Digital Readings Sensor."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .config_flow import CONF_API_KEY, CONF_CPE
from .const import DOMAIN
from .coordinator import ERedesDataCoordinator
from .core.sensors import CaptchaBalanceSensor, EnergyAccumulatorBalance


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configure all entities."""

    coordinator: ERedesDataCoordinator = hass.data[DOMAIN][
        entry.data[CONF_CPE] + "_coordinator"
    ]

    device_info = DeviceInfo(
        configuration_url="https://balcaodigital.e-redes.pt/home/consumptions",
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="E-Redes",
        name="E-Redes",
        model="Readings from E-Redes",
    )

    async_add_entities(
        [
            CaptchaBalanceSensor(
                device_info,
                user_cpe=entry.data[CONF_CPE],
                key_masked=entry.data[CONF_API_KEY][:4]
                + "*" * (len(entry.data[CONF_API_KEY]) - 8)
                + entry.data[CONF_API_KEY][-4:],
            )
        ],
        update_before_add=True,
    )

    async_add_entities(
        [
            EnergyAccumulatorBalance(
                device_info,
                user_cpe=entry.data[CONF_CPE],
                key_masked=entry.data[CONF_API_KEY][:4]
                + "*" * (len(entry.data[CONF_API_KEY]) - 8)
                + entry.data[CONF_API_KEY][-4:],
                coordinator=coordinator,
                coordinator_key=idx,
            )
            for idx in ("ponta", "cheia", "vazia")
        ],
        update_before_add=False,
    )
