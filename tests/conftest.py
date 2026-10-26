"""Synthetic BLE data and Home Assistant fixtures."""

from time import monotonic

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from custom_components.linkind_ble.const import MANUFACTURER_ID

ADDRESS = "AA:BB:CC:DD:EE:01"
OTHER_ADDRESS = "AA:BB:CC:DD:EE:02"


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow loading the integration under test."""


def payload(counter: int = 1, body: bytes = bytes(range(16))) -> bytes:
    """Create a synthetic frame, never a captured user's command body."""
    return bytes([counter, 2, 1]) + body


def service_info(
    frame: bytes | None = None,
    *,
    address: str = ADDRESS,
    source: str = "synthetic-proxy-1",
    rssi: int = -55,
    manufacturer_id: int = MANUFACTURER_ID,
) -> BluetoothServiceInfoBleak:
    """Create a non-connectable advertisement from a remote receiver."""
    data = {} if frame is None else {manufacturer_id: frame}
    return BluetoothServiceInfoBleak(
        name="",
        address=address,
        rssi=rssi,
        manufacturer_data=data,
        service_data={},
        service_uuids=[],
        source=source,
        device=BLEDevice(address, None, details={}),
        advertisement=AdvertisementData(
            local_name=None,
            manufacturer_data=data,
            service_data={},
            service_uuids=[],
            rssi=rssi,
            tx_power=-127,
            platform_data=(),
        ),
        connectable=False,
        time=monotonic(),
        tx_power=-127,
    )
