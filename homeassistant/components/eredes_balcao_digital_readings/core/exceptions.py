"""The E-Redes Balcao Digital Readings integration exceptions."""

from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Cannot connect to endpoint")


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Invalid Authentication Credentials")


class InvalidCaptchaAuthKey(HomeAssistantError):
    """Error to indicate there is invalid auth."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Invalid Captcha API Key")


class CaptchaFailedToConnectToApi(HomeAssistantError):
    """Error to indicate there is invalid auth."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Captcha Failed to Connect to API")


class CaptchaFailedToSolve(HomeAssistantError):
    """Error to indicate there is invalid auth."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Captcha Failed to Solve")
