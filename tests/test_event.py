"""Load the real HA event platform with a mocked radio boundary."""

from unittest.mock import Mock, patch

import pytest
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, STATE_UNKNOWN
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.linkind_ble.const import DOMAIN
from custom_components.linkind_ble.diagnostics import async_get_config_entry_diagnostics

from .conftest import ADDRESS, OTHER_ADDRESS, payload, service_info


@pytest.mark.usefixtures("mock_bluetooth")
async def test_activity_dedup_filter_unload_reload(hass):
    """A native entity receives fresh activity, deduplicates, and unsubscribes."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}, title="Test"
    )
    entry.add_to_hass(hass)
    unsubscribe = Mock()
    with patch(
        "custom_components.linkind_ble.event.bluetooth.async_register_callback",
        return_value=unsubscribe,
    ) as register:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id(
            "event", DOMAIN, f"{ADDRESS}_activity"
        )
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNKNOWN
        assert state.attributes["event_types"] == ["activity"]
        args, kwargs = register.call_args
        assert args[2] == {"address": ADDRESS, "connectable": False}
        assert args[3] is bluetooth.BluetoothScanningMode.PASSIVE
        assert kwargs["replay"] is bluetooth.BluetoothCallbackReplay.DISABLED
        receive = args[1]

        receive(
            service_info(payload(), address=OTHER_ADDRESS),
            bluetooth.BluetoothChange.ADVERTISEMENT,
        )
        receive(service_info(), bluetooth.BluetoothChange.ADVERTISEMENT)
        receive(service_info(b"bad"), bluetooth.BluetoothChange.ADVERTISEMENT)
        assert hass.states.get(entity_id).state == STATE_UNKNOWN
        receive(service_info(payload()), bluetooth.BluetoothChange.ADVERTISEMENT)
        first = hass.states.get(entity_id)
        assert first.state != STATE_UNKNOWN
        assert first.attributes["event_type"] == "activity"
        assert first.attributes["counter"] == 1
        assert first.attributes["rssi"] == -55
        assert "payload_hex" not in first.attributes

        receive(
            service_info(payload(), source="synthetic-proxy-2"),
            bluetooth.BluetoothChange.ADVERTISEMENT,
        )
        assert hass.states.get(entity_id) == first
        receive(service_info(payload(2)), bluetooth.BluetoothChange.ADVERTISEMENT)
        assert hass.states.get(entity_id).state != first.state

        device = dr.async_get(hass).async_get_device_by_identifier(
            (DOMAIN, ADDRESS), config_entry_id=entry.entry_id
        )
        assert device.manufacturer == "Linkind"
        assert device.model == "HCRZ12FBM071"
        diagnostics = await async_get_config_entry_diagnostics(hass, entry)
        assert diagnostics["decoder"]["accepted_frames"] == 2
        assert diagnostics["decoder"]["duplicate_frames"] == 1
        assert diagnostics["decoder"]["invalid_frames"] == 1
        assert ADDRESS not in str(diagnostics)
        assert "synthetic-proxy" not in str(diagnostics)

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        unsubscribe.assert_called_once()
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert register.call_count == 2
        assert entry.runtime_data.accepted == 0


@pytest.mark.usefixtures("mock_bluetooth")
async def test_two_devices_are_independent(hass):
    """Two buttons with identical frames each create their own activity."""
    with patch(
        "custom_components.linkind_ble.event.bluetooth.async_register_callback",
        return_value=Mock(),
    ) as register:
        for address in [ADDRESS, OTHER_ADDRESS]:
            entry = MockConfigEntry(
                domain=DOMAIN, unique_id=address, data={CONF_ADDRESS: address}
            )
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        for call in register.call_args_list:
            receive, matcher = call.args[1:3]
            receive(
                service_info(payload(), address=matcher["address"]),
                bluetooth.BluetoothChange.ADVERTISEMENT,
            )
        assert len(hass.states.async_all("event")) == 2
        assert all(
            state.attributes["counter"] == 1 for state in hass.states.async_all("event")
        )


@pytest.mark.usefixtures("mock_bluetooth")
async def test_documented_automation_first_event_and_reload(hass):
    """The recommended trigger fires on the first activity, never on restoration."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}
    )
    entry.add_to_hass(hass)
    actions = Mock()
    hass.services.async_register("test", "record", actions)
    with patch(
        "custom_components.linkind_ble.event.bluetooth.async_register_callback",
        return_value=Mock(),
    ) as register:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id(
            "event", DOMAIN, f"{ADDRESS}_activity"
        )
        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "alias": "Example activity automation",
                    "triggers": [
                        {
                            "trigger": "event.received",
                            "target": {"entity_id": entity_id},
                            "options": {"event_type": ["activity"]},
                        }
                    ],
                    "actions": [{"action": "test.record"}],
                }
            },
        )
        await hass.async_block_till_done()
        assert actions.call_count == 0
        receive = register.call_args.args[1]
        receive(service_info(payload()), bluetooth.BluetoothChange.ADVERTISEMENT)
        await hass.async_block_till_done()
        assert actions.call_count == 1
        receive(service_info(payload()), bluetooth.BluetoothChange.ADVERTISEMENT)
        await hass.async_block_till_done()
        assert actions.call_count == 1
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert actions.call_count == 1
        register.call_args.args[1](
            service_info(payload(2)), bluetooth.BluetoothChange.ADVERTISEMENT
        )
        await hass.async_block_till_done()
        assert actions.call_count == 2


@pytest.mark.usefixtures("mock_bluetooth")
async def test_real_bluetooth_manager_no_cached_replay(hass):
    """The real Bluetooth callback route accepts remote, non-connectable data."""
    assert await async_setup_component(hass, "bluetooth", {})
    receive = bluetooth.async_get_advertisement_callback(hass)
    receive(service_info(payload()))
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "event", DOMAIN, f"{ADDRESS}_activity"
    )
    assert hass.states.get(entity_id).state == STATE_UNKNOWN
    receive(service_info(payload(2)))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes["counter"] == 2
    receive(service_info(payload(2), source="synthetic-proxy-2", rssi=-40))
    await hass.async_block_till_done()
    assert entry.runtime_data.accepted == 1
