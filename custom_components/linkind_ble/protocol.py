"""Parse observed activity frames without interpreting the opaque command body.

This module has no Home Assistant or Bluetooth dependencies. Its fixtures are
synthetic; see docs/protocol.md for the evidence and limits of the decoder.
"""

from collections import OrderedDict
from dataclasses import dataclass

from .const import REPEAT_WINDOW

MAX_RECENT_FRAMES = 256


@dataclass(frozen=True, slots=True)
class Activity:
    """A new activity frame, not a decoded gesture."""

    counter: int


def parse_activity(payload: bytes) -> Activity | None:
    """Recognize the observed frame layout; this is not model authentication."""
    if len(payload) != 19 or payload[1:3] != b"\x02\x01":
        return None
    return Activity(counter=payload[0])


class ActivityDecoder:
    """Collapse repeated full frames using a sliding quiet period."""

    def __init__(self, repeat_window: float = REPEAT_WINDOW) -> None:
        """Initialize a bounded cache for one configured device."""
        if repeat_window <= 0:
            raise ValueError("repeat_window must be positive")
        self.repeat_window = repeat_window
        self._recent: OrderedDict[bytes, float] = OrderedDict()
        self.accepted = 0
        self.duplicates = 0
        self.invalid = 0

    def process(self, payload: bytes, now: float) -> Activity | None:
        """Return activity only for a valid frame absent during the quiet period.

        Use monotonic receive time, shared across receivers. Comparing the entire
        frame permits counter wrap and different bodies with the same counter.
        """
        activity = parse_activity(payload)
        if activity is None:
            self.invalid += 1
            return None

        while self._recent:
            oldest, last_seen = next(iter(self._recent.items()))
            if now - last_seen < self.repeat_window:
                break
            del self._recent[oldest]

        repeated = payload in self._recent
        self._recent[payload] = now
        self._recent.move_to_end(payload)
        if len(self._recent) > MAX_RECENT_FRAMES:
            self._recent.popitem(last=False)
        if repeated:
            self.duplicates += 1
            return None
        self.accepted += 1
        return activity

    def diagnostics(self) -> dict[str, int | float]:
        """Return counters without device identifiers or advertisement contents."""
        return {
            "accepted_frames": self.accepted,
            "duplicate_frames": self.duplicates,
            "invalid_frames": self.invalid,
            "repeat_window_seconds": self.repeat_window,
        }
