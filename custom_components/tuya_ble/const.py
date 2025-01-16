"""Constants for Tuya BLE integration."""
from dataclasses import dataclass

DOMAIN = "tuya_ble"

# BLE Service UUID
TUYA_BLE_SERVICE = "0000fd50-0000-1001-8001-00805f9b07d0"
TUYA_MANUFACTURER_ID = 2000

# Light specific constants
LIGHT_DP_ID = {
    "SWITCH": 0x01,      # Switch
    "BRIGHT": 0x02,      # Brightness
    "TEMP": 0x03,        # Color Temperature
}

@dataclass
class TuyaBLEDevice:
    """Tuya BLE device information."""
    mac: str
    name: str
    model: str | None = None
