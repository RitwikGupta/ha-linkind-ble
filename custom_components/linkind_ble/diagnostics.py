"""Diagnostics that omit addresses, names, receiver IDs, and raw payloads."""

from typing import Any

from homeassistant.core import HomeAssistant

from . import LinkindConfigEntry
from .const import MODEL


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LinkindConfigEntry
) -> dict[str, Any]:
    """Return only model information and decoder counters."""
    return {"model": MODEL, "decoder": entry.runtime_data.diagnostics()}
