"""Constants for Tuya BLE integration."""
from dataclasses import dataclass

@dataclass
class TuyaBLEDevice:
    """Tuya BLE device information."""
    mac: str
    name: str
    model: str | None = None
