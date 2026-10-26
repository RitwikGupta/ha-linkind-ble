"""Verify discovery, exact-model confirmation, and duplicate prevention."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.linkind_ble.const import DOMAIN

from .conftest import ADDRESS, payload, service_info


@pytest.mark.usefixtures("mock_bluetooth")
async def test_discovery_and_confirmation(hass):
    """Discovery requires explicit model confirmation before creating an entry."""
    with patch("custom_components.linkind_ble.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info(payload())
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "bluetooth_confirm"
        assert not hass.config_entries.async_entries(DOMAIN)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == {CONF_ADDRESS: ADDRESS}
        assert result["result"].unique_id == ADDRESS
        await hass.async_block_till_done()


@pytest.mark.parametrize("frame", [None, b"wrong", payload()[:-1]])
async def test_reject_discovery(hass, frame):
    """Manufacturer ID alone does not authorize device creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info(frame)
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_duplicate_discovery(hass):
    """One Bluetooth address has only one entry, including lowercase input."""
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info(payload(), address=ADDRESS.lower()),
    )
    assert result["reason"] == "already_configured"


async def test_manual_selection_and_confirmation(hass):
    """Select a discovered device and still confirm its physical model."""
    with (
        patch("custom_components.linkind_ble.async_setup_entry", return_value=True),
        patch(
            "custom_components.linkind_ble.config_flow.bluetooth.async_discovered_service_info",
            return_value=[service_info(payload()), service_info(b"bad")],
        ) as discovered,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        discovered.assert_called_with(hass, False)
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: ADDRESS}
        )
        assert result["step_id"] == "bluetooth_confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()


async def test_no_unconfigured_candidates(hass):
    """Only valid, unconfigured frames appear in the picker."""
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    with patch(
        "custom_components.linkind_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[service_info(payload()), service_info(b"bad")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["reason"] == "no_devices_found"


async def test_stale_selection(hass):
    """An address not offered by this flow cannot be submitted directly."""
    with patch(
        "custom_components.linkind_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[service_info(payload())],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        with pytest.raises(InvalidData):
            await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_ADDRESS: "AA:BB:CC:DD:EE:99"}
            )
