"""Discover candidate advertisements and confirm the exact button model."""

from typing import Any

import probatio
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, MANUFACTURER_ID, device_name
from .protocol import parse_activity


def is_candidate(info: bluetooth.BluetoothServiceInfoBleak) -> bool:
    """Check the observed layout; unrelated products may share this signature."""
    payload = info.manufacturer_data.get(MANUFACTURER_ID)
    return payload is not None and parse_activity(payload) is not None


class LinkindConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one confirmed button, identified by its Bluetooth address."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize discovery state."""
        self._address = ""
        self._candidates: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery, including non-connectable proxies."""
        if not is_candidate(discovery_info):
            return self.async_abort(reason="not_supported")
        self._address = discovery_info.address.upper()
        await self.async_set_unique_id(self._address)
        self._abort_if_unique_id_configured()
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Require confirmation because the radio signature is not model proof."""
        name = device_name(self._address)
        if user_input is not None:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name, data={CONF_ADDRESS: self._address}
            )
        self._set_confirm_only()
        self.context["title_placeholders"] = {"name": name}
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": name, "address": self._address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a matching device seen by Home Assistant's Bluetooth system."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            self._address = address
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_bluetooth_confirm()

        configured = self._async_current_ids(include_ignore=False)
        self._candidates = {
            info.address.upper(): f"{device_name(info.address)} ({info.address})"
            for info in bluetooth.async_discovered_service_info(self.hass, False)
            if info.address.upper() not in configured and is_candidate(info)
        }
        if not self._candidates:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {probatio.Required(CONF_ADDRESS): probatio.In(self._candidates)}
            ),
        )
