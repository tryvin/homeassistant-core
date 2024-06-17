"""Constants for the E-Redes Balcao Digital Readings integration."""

from datetime import timedelta
import logging
from typing import Final

from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME  # noqa: F401

DOMAIN: Final = "eredes_balcao_digital_readings"
DEFAULT_TIMEOUT: Final = timedelta(seconds=60)
CONF_CPE: Final = "eredes_cpe"
CONF_CAPTCHA_API_ENDPOINT: Final = "eredes_captcha_api_endpoint"

_LOGGER = logging.getLogger(__name__)

USER_AGENT: Final = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
HOME_URL: Final = "https://balcaodigital.e-redes.pt/"
ORIGIN_URL: Final = "https://balcaodigital.e-redes.pt"
DEFAULT_HEADERS: Final = {
    "User-Agent": USER_AGENT,
}
