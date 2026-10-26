"""Exercise the observed frame envelope and repeat behavior."""

import pytest

from custom_components.linkind_ble.protocol import (
    MAX_RECENT_FRAMES,
    ActivityDecoder,
    parse_activity,
)

from .conftest import payload


@pytest.mark.parametrize(
    "frame",
    [b"", b"\x01", payload()[:-1], payload() + b"\x00", b"\x01\x01\x02" + bytes(16)],
)
def test_reject_malformed(frame):
    """Unknown layouts never create activity."""
    decoder = ActivityDecoder()
    assert parse_activity(frame) is None
    assert decoder.process(frame, 0) is None
    assert decoder.diagnostics()["invalid_frames"] == 1


def test_six_bursts_many_receivers():
    """Hundreds of repeated callbacks still yield six distinct frames."""
    decoder = ActivityDecoder()
    accepted = []
    for counter in range(6):
        for index in range(83):
            if activity := decoder.process(payload(counter), counter * 5 + index / 20):
                accepted.append(activity.counter)
    assert accepted == list(range(6))
    assert decoder.accepted == 6
    assert decoder.duplicates == 492


def test_sliding_quiet_period_and_interleaved_repeats():
    """Repeats refresh their own timer even when another frame intervenes."""
    decoder = ActivityDecoder()
    assert decoder.process(payload(1), 0)
    assert decoder.process(payload(2), 1)
    assert decoder.process(payload(1), 9) is None
    assert decoder.process(payload(1), 18) is None
    assert decoder.process(payload(1), 28)
    assert decoder.process(payload(2), 29)


def test_wrap_body_identity_and_device_isolation():
    """Counters can wrap or repeat; each device has an independent decoder."""
    first, second = ActivityDecoder(), ActivityDecoder()
    for counter in [254, 255, 0, 1]:
        assert first.process(payload(counter), 0)
    assert first.process(payload(1, bytes(reversed(range(16)))), 1)
    assert second.process(payload(1), 1)
    assert first.process(payload(1), 2) is None


def test_cache_is_bounded():
    """Unexpected bursts cannot grow the per-device repeat cache indefinitely."""
    decoder = ActivityDecoder()
    for index in range(MAX_RECENT_FRAMES + 10):
        assert decoder.process(payload(0, index.to_bytes(16, "big")), 0)
    assert len(decoder._recent) == MAX_RECENT_FRAMES


def test_invalid_repeat_window():
    """Reject a decoder setting that would disable repeat suppression."""
    with pytest.raises(ValueError, match="positive"):
        ActivityDecoder(0)
