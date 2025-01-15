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

from .const import DOMAIN
from .tuya_ble import TuyaBLEData, TuyaBLEEntity

_LOGGER = logging.getLogger(__name__)

# Tuya BLE Protocol Constants
CMD_ON = 0x01
CMD_OFF = 0x00
CMD_BRIGHTNESS = 0x02
CMD_COLOR_TEMP = 0x03

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya BLE lights."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    if data.device:  # Use existing TuyaBLEDevice instance
        entities.append(TuyaBLELight(data.device))
    
    async_add_entities(entities)

class TuyaBLELight(TuyaBLEEntity, LightEntity):
    """Tuya BLE light device."""

    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, device) -> None:
        """Initialize the light."""
        super().__init__(device)
        self._attr_unique_id = f"{device.address}_light"
        self._attr_name = f"Tuya Light {device.address[-6:]}"
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
            # Ensure connection using existing TuyaBLEDevice connection handling
            await self.device._ensure_connected()
            
            # Build command packet
            command = bytearray([CMD_ON])
            
            if ATTR_BRIGHTNESS in kwargs:
                brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
                command.extend([CMD_BRIGHTNESS, brightness])
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                
            if ATTR_COLOR_TEMP in kwargs:
                temp = int((kwargs[ATTR_COLOR_TEMP] - 153) * 100 / 347)
                command.extend([CMD_COLOR_TEMP, temp])
                self._color_temp = kwargs[ATTR_COLOR_TEMP]
            
            # Send command using existing send_packet method
            await self.device._send_packet_while_connected(
                self.device.TuyaBLECode.FUN_SENDER_CONTROL,
                command,
                0,
                True
            )
            self._is_on = True
            
        except Exception as error:
            _LOGGER.error("Error turning on light: %s", error)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.device._ensure_connected()
            command = bytearray([CMD_OFF])
            await self.device._send_packet_while_connected(
                self.device.TuyaBLECode.FUN_SENDER_CONTROL,
                command,
                0,
                True
            )
            self._is_on = False
        except Exception as error:
            _LOGGER.error("Error turning off light: %s", error)

    def _handle_notification(self, data: bytes) -> None:
        """Handle incoming data from the device."""
        # Example notification handler - adjust based on your device's protocol
        try:
            if data[0] == CMD_ON:
                self._is_on = True
            elif data[0] == CMD_OFF:
                self._is_on = False
            elif data[0] == CMD_BRIGHTNESS:
                self._brightness = int(data[1] * 255 / 100)
            elif data[0] == CMD_COLOR_TEMP:
                self._color_temp = int(data[1] * 347 / 100 + 153)
            
            self.async_write_ha_state()
        except Exception as error:
            _LOGGER.error("Error handling notification: %s", error)
