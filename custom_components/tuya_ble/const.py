"""Constants for Tuya BLE integration."""
from dataclasses import dataclass

DOMAIN = "tuya_ble"

# Configuration constants
CONF_PRODUCT_MODEL = "product_model"
CONF_UUID = "uuid"
CONF_LOCAL_KEY = "local_key"
CONF_CATEGORY = "category"
CONF_PRODUCT_ID = "product_id"
CONF_DEVICE_NAME = "device_name"
CONF_PRODUCT_NAME = "product_name"
CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_AUTH_TYPE = "auth_type"

# Tuya API URLs
TUYA_API_DEVICES_URL = "/v1.0/devices"
TUYA_API_FACTORY_INFO_URL = "/v1.0/devices/factory-infos"
TUYA_FACTORY_INFO_MAC = "mac"

# App types
SMARTLIFE_APP = "smartlife"

# BLE Service UUID
TUYA_BLE_SERVICE = "0000fd50-0000-1001-8001-00805f9b07d0"

@dataclass
class TuyaBLEDevice:
    """Tuya BLE device information."""
    mac: str
    name: str
    model: str | None = None
