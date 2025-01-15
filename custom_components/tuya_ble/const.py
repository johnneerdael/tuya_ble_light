"""Constants for Tuya BLE integration."""
from dataclasses import dataclass
from enum import Enum

class TuyaRegion(Enum):
    """Tuya device regions."""
    AMERICA = "America"
    EUROPE = "Europe"
    CHINA = "China"
    INDIA = "India"
    EASTERN_AMERICA = "Eastern America"
    WESTERN_EUROPE = "Western Europe"

@dataclass
class TuyaBLEDevice:
    """Tuya BLE device information."""
    mac: str
    name: str
    model: str | None = None
    region: TuyaRegion | None = None
