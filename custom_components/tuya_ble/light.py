"""Support for Tuya BLE lights."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TuyaBLEDevice
from .tuya_ble import TuyaBLEEntity

_LOGGER = logging.getLogger(__name__)

# Tuya BLE Protocol Constants for Lighting
LIGHT_CMD = {
    "ON": 0x01,
    "OFF": 0x00,
    "BRIGHTNESS": 0x02,
    "COLOR_TEMP": 0x03,
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tuya BLE light based on config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    
    if data.device:
        async_add_entities([TuyaBLELight(data.device)])

class TuyaBLELight(TuyaBLEEntity, LightEntity):
    """Tuya BLE light device."""

    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, device: TuyaBLEDevice) -> None:
        """Initialize the light."""
        super().__init__(device)
        self._attr_unique_id = f"{device.mac}_light"
        self._attr_name = device.name or f"Tuya Light {device.mac[-6:]}"
        self._is_on = False
        self._brightness = 0
        self._color_temp = 0

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def color_temp(self) -> int | None:
        """Return the color temperature in mireds."""
        return self._color_temp

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        try:
            await self.device.ensure_connected()
            
            command = bytearray([LIGHT_CMD["ON"]])
            
            if ATTR_BRIGHTNESS in kwargs:
                brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
                command.extend([LIGHT_CMD["BRIGHTNESS"], brightness])
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                
            if ATTR_COLOR_TEMP in kwargs:
                temp = int((kwargs[ATTR_COLOR_TEMP] - 153) * 100 / 347)
                command.extend([LIGHT_CMD["COLOR_TEMP"], temp])
                self._color_temp = kwargs[ATTR_COLOR_TEMP]
            
            await self.device.send_command(command)
            self._is_on = True
            
        except Exception as error:
            _LOGGER.error("Error turning on light: %s", error)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.device.ensure_connected()
            await self.device.send_command(bytearray([LIGHT_CMD["OFF"]]))
            self._is_on = False
        except Exception as error:
            _LOGGER.error("Error turning off light: %s", error)
