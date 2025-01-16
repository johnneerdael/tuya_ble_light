"""Config flow for Tuya BLE."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import async_discovered_service_info, BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, TUYA_BLE_SERVICE, TUYA_MANUFACTURER_ID

_LOGGER = logging.getLogger(__name__)

def get_device_info(discovery_info: BluetoothServiceInfoBleak) -> str:
    """Get formatted device info for display."""
    name = discovery_info.name or "Unknown"
    mac = discovery_info.address
    short_mac = mac[-6:].replace(":", "")
    rssi = discovery_info.rssi
    return f"{name} ({short_mac}) RSSI: {rssi}dBm"

class TuyaBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection."""
        errors = {}

        if not self._discovered_devices:
            for discovery_info in async_discovered_service_info(self.hass):
                if (
                    TUYA_BLE_SERVICE in discovery_info.service_uuids
                    and discovery_info.manufacturer_data.get(TUYA_MANUFACTURER_ID, b"").startswith(b"\x00")
                ):
                    self._discovered_devices.append(discovery_info)
                    _LOGGER.debug(
                        "Found Tuya BLE device: %s, RSSI: %d, Manufacturer Data: %s",
                        discovery_info.address,
                        discovery_info.rssi,
                        discovery_info.manufacturer_data,
                    )

        if not self._discovered_devices:
            return self.async_abort(reason="no_unconfigured_devices")

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, f"Tuya Light {address[-6:]}"),
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: user_input.get(CONF_NAME, f"Tuya Light {address[-6:]}")
                },
            )

        # Sort devices by signal strength
        self._discovered_devices.sort(key=lambda x: x.rssi, reverse=True)
        
        devices = {
            discovery_info.address: get_device_info(discovery_info)
            for discovery_info in self._discovered_devices
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): vol.In(devices),
                vol.Optional(CONF_NAME): str,
            }),
            errors=errors,
        )