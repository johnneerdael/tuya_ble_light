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

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya BLE lights."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    for device in data.devices:
        if device.category == "dj":  # Light category
            entities.append(TuyaBLELight(device, data.device_info))
    
    async_add_entities(entities)

class TuyaBLELight(TuyaBLEEntity, LightEntity):
    """Tuya BLE light device."""

    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, device, device_info):
        """Initialize the light."""
        super().__init__(device, device_info)
        self._attr_unique_id = f"{device.uuid}_light"
        self._attr_name = f"{device.name} Light"

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.device.datapoints.get("switch_led", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        bright = self.device.datapoints.get("bright_value_v2")
        if bright is not None:
            return int(bright * 255 / 100)
        return None

    @property
    def color_temp(self) -> int | None:
        """Return the color temperature in mireds."""
        temp = self.device.datapoints.get("temp_value_v2")
        if temp is not None:
            # Convert the device's color temp value to mireds
            # You may need to adjust the conversion based on your device's range
            return int(temp * 347 / 100 + 153)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if not self.is_on:
            await self.device.set_dp("switch_led", True)

        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self.device.set_dp("bright_value_v2", brightness)

        if ATTR_COLOR_TEMP in kwargs:
            temp = int((kwargs[ATTR_COLOR_TEMP] - 153) * 100 / 347)
            await self.device.set_dp("temp_value_v2", temp)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.device.set_dp("switch_led", False)
