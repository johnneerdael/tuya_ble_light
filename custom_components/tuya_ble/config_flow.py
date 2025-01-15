"""Config flow for Tuya BLE."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ACCESS_ID, CONF_ACCESS_SECRET, CONF_ADDRESS, CONF_ENDPOINT
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, TUYA_BLE_SERVICE
from .cloud import HASSTuyaBLEDeviceManager

_LOGGER = logging.getLogger(__name__)

REGION_ENDPOINTS = {
    "America": "https://openapi.tuyaus.com",
    "Europe": "https://openapi.tuyaeu.com",
    "China": "https://openapi.tuyacn.com",
    "India": "https://openapi.tuyain.com",
    "Eastern America": "https://openapi-ueaz.tuyaus.com",
    "Western Europe": "https://openapi-weaz.tuyaeu.com",
}

class TuyaBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices = []
        self._auth_data = {}
        self._manager: HASSTuyaBLEDeviceManager | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle IoT platform credentials input."""
        errors = {}

        if user_input is not None:
            # Initialize device manager if not already done
            if not self._manager:
                self._manager = HASSTuyaBLEDeviceManager(self.hass)

            # Add endpoint based on selected region
            region = user_input["region"]
            auth_data = {
                CONF_ACCESS_ID: user_input[CONF_ACCESS_ID],
                CONF_ACCESS_SECRET: user_input[CONF_ACCESS_SECRET],
                CONF_ENDPOINT: REGION_ENDPOINTS[region],
            }

            # Validate credentials
            try:
                response = await self._manager._login(auth_data, True)
                if not self._manager._is_login_success(response):
                    _LOGGER.error("Failed to validate IoT credentials: %s", response)
                    errors["base"] = "invalid_auth"
                else:
                    self._auth_data = auth_data
                    return await self.async_step_device()
            except Exception as err:
                _LOGGER.exception("Unexpected error validating credentials")
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_ID): str,
                    vol.Required(CONF_ACCESS_SECRET): str,
                    vol.Required("region"): vol.In(REGION_ENDPOINTS),
                }
            ),
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection."""
        errors = {}

        if not self._discovered_devices:
            for discovery_info in async_discovered_service_info(self.hass):
                if TUYA_BLE_SERVICE in discovery_info.service_uuids:
                    self._discovered_devices.append(discovery_info)

        if not self._discovered_devices:
            return self.async_abort(reason="no_unconfigured_devices")

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            
            # Validate device is registered in IoT platform
            try:
                if self._manager:
                    # You might want to add a method to verify the device exists
                    # in your IoT project here
                    pass
            except Exception:
                errors["base"] = "device_not_registered"
            else:
                await self.async_set_unique_id(address)
                return self.async_create_entry(
                    title=f"Tuya BLE {address[-6:]}",
                    data={**self._auth_data, CONF_ADDRESS: address},
                )

        devices = {
            discovery_info.address: f"{discovery_info.name} ({discovery_info.address})"
            for discovery_info in self._discovered_devices
        }

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(devices)}),
            errors=errors,
        )