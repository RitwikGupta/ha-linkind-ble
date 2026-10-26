"""Local activity detection for the Linkind HCRZ12FBM071 BLE button."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .protocol import ActivityDecoder

type LinkindConfigEntry = ConfigEntry[ActivityDecoder]

PLATFORMS = [Platform.EVENT]


async def async_setup_entry(hass: HomeAssistant, entry: LinkindConfigEntry) -> bool:
    """Set up a button with its own duplicate suppression state."""
    entry.runtime_data = ActivityDecoder()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LinkindConfigEntry) -> bool:
    """Unload the entity and its Bluetooth subscription."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
