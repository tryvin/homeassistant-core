"""Common fixtures for the E-Redes Balcao Digital Readings tests."""

from unittest.mock import AsyncMock, patch

import pytest
from typing_extensions import Generator


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.eredes_balcao_digital_readings.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
