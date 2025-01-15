"""Support for Tuya BLE lights."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, TuyaBLEDevice
from .tuya_ble import TuyaBLEEntity

_LOGGER = logging.getLogger(__name__)

# Update service and characteristic UUIDs based on your device
TUYA_SERVICE_UUID = "0000fd50-0000-1001-8001-00805f9b07d0"
TUYA_WRITE_CHARACTERISTIC = "00000001-0000-1001-8001-00805f9b07d0"
TUYA_NOTIFY_CHARACTERISTIC = "00000002-0000-1001-8001-00805f9b07d0"

# Tuya BLE Protocol Constants for Lighting
LIGHT_DP_ID = {
    "SWITCH": 0x01,      # Switch
    "BRIGHT": 0x02,      # Brightness
    "TEMP": 0x03,        # Color Temperature
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

class TuyaBLELight(TuyaBLEEntity, LightEntity, RestoreEntity):
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
        self._manufacturer_data = "0x00000100D320323A40B54E4004C889B00BEEE0A1"
        self._last_update = 0
        self._state_cache = {}
        self._available = True

    async def async_added_to_hass(self) -> None:
        """Handle entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state if available
        last_state = await self.async_get_last_state()
        if last_state:
            self._is_on = last_state.state == "on"
            if last_state.attributes.get(ATTR_BRIGHTNESS):
                self._brightness = last_state.attributes[ATTR_BRIGHTNESS]
            if last_state.attributes.get(ATTR_COLOR_TEMP):
                self._color_temp = last_state.attributes[ATTR_COLOR_TEMP]
            
            # Cache the restored state
            self._state_cache = {
                "state": self._is_on,
                "brightness": self._brightness,
                "color_temp": self._color_temp,
                "timestamp": time.time()
            }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available and super().available

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

    def _cache_state(self) -> None:
        """Cache the current state."""
        self._state_cache = {
            "state": self._is_on,
            "brightness": self._brightness,
            "color_temp": self._color_temp,
            "timestamp": time.time()
        }

    def _restore_cached_state(self) -> None:
        """Restore state from cache if recent."""
        if self._state_cache and time.time() - self._state_cache["timestamp"] < 300:  # 5 minutes
            self._is_on = self._state_cache["state"]
            self._brightness = self._state_cache["brightness"]
            self._color_temp = self._state_cache["color_temp"]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.connected:
            self._available = True
        else:
            self._available = False
            self._restore_cached_state()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        try:
            await self.device.ensure_connected()
            
            # Build the command packet according to the protocol
            command = self.device._build_packets(
                seq_num=self.device._get_sequence_number(),
                code=self.device.TuyaBLECode.FUN_SENDER_CONTROL,
                data=bytes([
                    LIGHT_DP_ID["SWITCH"],  # DP ID
                    0x01,                   # Type (bool)
                    0x01,                   # Length
                    0x01                    # Value (ON)
                ])
            )
            
            # Send the command
            for packet in command:
                await self.device._write_packet(packet)
            
            if ATTR_BRIGHTNESS in kwargs:
                brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
                bright_command = self.device._build_packets(
                    seq_num=self.device._get_sequence_number(),
                    code=self.device.TuyaBLECode.FUN_SENDER_CONTROL,
                    data=bytes([
                        LIGHT_DP_ID["BRIGHT"],  # DP ID
                        0x02,                   # Type (value)
                        0x04,                   # Length
                        brightness              # Value
                    ])
                )
                for packet in bright_command:
                    await self.device._write_packet(packet)
                self._brightness = kwargs[ATTR_BRIGHTNESS]
            
            self._is_on = True
            self._cache_state()
            self.async_write_ha_state()
            
        except Exception as error:
            _LOGGER.error("Error turning on light: %s", error)
            self._available = False
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.device.ensure_connected()
            
            command = self.device._build_packets(
                seq_num=self.device._get_sequence_number(),
                code=self.device.TuyaBLECode.FUN_SENDER_CONTROL,
                data=bytes([
                    LIGHT_DP_ID["SWITCH"],  # DP ID
                    0x01,                   # Type (bool)
                    0x01,                   # Length
                    0x00                    # Value (OFF)
                ])
            )
            
            for packet in command:
                await self.device._write_packet(packet)
            
            self._is_on = False
            self._cache_state()
            self.async_write_ha_state()
        except Exception as error:
            _LOGGER.error("Error turning off light: %s", error)
            self._available = False
            self.async_write_ha_state()

    def _handle_notification(self, data: bytes) -> None:
        """Handle incoming data from the device."""
        try:
            # Parse the datapoints using the existing method
            self.device._parse_datapoints_v3(time.time(), 0, data, 0)
            
            # Update our state based on the parsed data
            if LIGHT_DP_ID["SWITCH"] in self.device._datapoints:
                self._is_on = self.device._datapoints[LIGHT_DP_ID["SWITCH"]].value
            
            if LIGHT_DP_ID["BRIGHT"] in self.device._datapoints:
                self._brightness = int(self.device._datapoints[LIGHT_DP_ID["BRIGHT"]].value * 255 / 100)
            
            if LIGHT_DP_ID["TEMP"] in self.device._datapoints:
                self._color_temp = int(self.device._datapoints[LIGHT_DP_ID["TEMP"]].value * 347 / 100 + 153)
            
            self._available = True
            self._cache_state()
            self.async_write_ha_state()
            
        except Exception as error:
            _LOGGER.error("Error handling notification: %s", error)
