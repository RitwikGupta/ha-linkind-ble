"""Expose observed activity as a native Home Assistant event entity."""

from time import monotonic

from homeassistant.components import bluetooth
from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LinkindConfigEntry
from .const import (
    DOMAIN,
    EVENT_ACTIVITY,
    MANUFACTURER,
    MANUFACTURER_ID,
    MODEL,
    device_name,
)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LinkindConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the activity entity."""
    async_add_entities([LinkindActivityEvent(entry)])


class LinkindActivityEvent(EventEntity):
    """An activity timestamp; the opaque command body is deliberately unused."""

    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = [EVENT_ACTIVITY]
    _attr_has_entity_name = True
    _attr_translation_key = "button_activity"

    def __init__(self, entry: LinkindConfigEntry) -> None:
        """Initialize the per-device entity."""
        self._address: str = entry.data[CONF_ADDRESS]
        self._decoder = entry.runtime_data
        self._attr_unique_id = f"{self._address}_activity"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._address)},
            connections={(dr.CONNECTION_BLUETOOTH, self._address)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=device_name(self._address),
        )

    async def async_added_to_hass(self) -> None:
        """Listen after the entity exists; never replay cached advertisements."""
        await super().async_added_to_hass()
        self.async_on_remove(
            bluetooth.async_register_callback(
                self.hass,
                self._async_handle_advertisement,
                {"address": self._address, "connectable": False},
                bluetooth.BluetoothScanningMode.PASSIVE,
                replay=bluetooth.BluetoothCallbackReplay.DISABLED,
            )
        )

    @callback
    def _async_handle_advertisement(
        self,
        info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Process only this device's manufacturer data across all receivers."""
        if info.address.upper() != self._address:
            return
        payload = info.manufacturer_data.get(MANUFACTURER_ID)
        if payload is None:
            return
        if (activity := self._decoder.process(payload, monotonic())) is None:
            return
        self._trigger_event(
            EVENT_ACTIVITY, {"counter": activity.counter, "rssi": info.rssi}
        )
        self.async_write_ha_state()
