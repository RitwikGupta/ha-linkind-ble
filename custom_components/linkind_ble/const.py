"""Constants for the Linkind BLE integration."""

DOMAIN = "linkind_ble"
MANUFACTURER = "Linkind"
MODEL = "HCRZ12FBM071"
MANUFACTURER_ID = 0x1511
EVENT_ACTIVITY = "activity"
REPEAT_WINDOW = 10.0


def device_name(address: str) -> str:
    """Give each button a short, recognizable default name."""
    return f"Linkind button {address.replace(':', '')[-6:]}"
