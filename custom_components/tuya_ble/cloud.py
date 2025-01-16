"""Tuya BLE cloud interface."""
from __future__ import annotations

import logging
from typing import Any

from tuya_iot import TuyaOpenAPI, AuthType

from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_ENDPOINT,
    TUYA_API_DEVICES_URL,
    TUYA_API_FACTORY_INFO_URL,
    TUYA_FACTORY_INFO_MAC,
    TUYA_RESPONSE_SUCCESS,
    TUYA_RESPONSE_RESULT,
)

_LOGGER = logging.getLogger(__name__)

class HASSTuyaBLEDeviceManager:
    """Manage Tuya BLE devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._hass = hass
        self._api: TuyaOpenAPI | None = None

    async def _login(self, auth_data: dict[str, Any], force: bool = False) -> dict[str, Any]:
        """Login to Tuya IoT Platform."""
        if not self._api or force:
            self._api = TuyaOpenAPI(
                auth_data[CONF_ENDPOINT],
                auth_data[CONF_ACCESS_ID],
                auth_data[CONF_ACCESS_SECRET],
                auth_type=AuthType.CUSTOM
            )
            return await self._hass.async_add_executor_job(self._api.connect)
        return {"success": True}

    def _is_login_success(self, response: dict[str, Any]) -> bool:
        """Check if login was successful."""
        return response.get(TUYA_RESPONSE_SUCCESS, False)
