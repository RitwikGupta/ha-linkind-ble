# Observed Linkind HCRZ12FBM071 advertisements

This document describes observations from one physical button. It is not a
vendor protocol specification. The initial listener used macOS CoreBluetooth
through Bleak; a later check confirmed that HA received the same frame format
through an ESP32-C5 ESPHome Bluetooth proxy.

## Manufacturer data envelope

Home Assistant and Bleak expose the advertisement's manufacturer section as a
dictionary. The relevant key was `0x1511` (decimal `5393`). That number is an
observed field value, not an independently verified Bluetooth SIG company
assignment or a unique product identifier.

The dictionary value was exactly **19 bytes**, excluding the two-byte
manufacturer field:

| Offset | Length | Observation | Interpretation used here |
| --- | --- | --- | --- |
| 0 | 1 | Incremented between observed actions | Counter byte only |
| 1 | 2 | `02 01` in all recorded matching frames | Layout discriminator |
| 3 | 16 | Varied across frames | Opaque body, ignored |

A synthetic value, never captured from a device:

```text
01 02 01 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
```

In the raw advertising data, the manufacturer field uses little endian order
`11 15`. Do not prepend those bytes when passing HA's manufacturer dictionary
value to `parse_activity`.

The 16-byte body could encode commands, authentication, encrypted material, or
something else. Its appearance and length do not establish encryption. No
decryption, key derivation, command meaning, or connection protocol is claimed.

## Evidence and event semantics

- An initial trial of six instructed single front-button presses produced six
  distinct consecutive frames among hundreds of repeated callbacks.
- Identical frames were repeated for roughly two to five seconds.
- A mixed double-press/hold trial produced additional frames, but the timing was
  insufficiently isolated to label them as particular gestures.
- A later isolated one-press validation produced one deduplicated activity.
- A separate instructed three-press trial produced four distinct frames, so
  exact one-to-one behavior must not be generalized to every interaction.
- The proxy check established reception of the same envelope inside HA; it did
  not validate gesture semantics or all possible firmware revisions.

The public fixtures reproduce the layout and repeat timing with invented bodies.
Raw research captures include private device identifiers and are not committed.
Counter wrap is tested synthetically, not yet established in a live wrap trial.

## Duplicate suppression

One decoder belongs to each configured address. It compares complete payloads,
not only the counter, across receivers. An identical frame updates its last-seen
time and is suppressed until it has been absent from delivered callbacks for at
least ten seconds. Distinct payloads are accepted immediately, including those
with an identical counter or a counter that wraps from 255 to 0.

The recent-frame cache is limited to 256 payloads per device. This is a memory
bound; an extreme burst can evict frames sooner than the quiet period. The
algorithm is intended for the observed low-rate remote traffic, not malicious
traffic. It provides no authentication or durable replay protection.

HA callbacks can coalesce unchanged advertisements. Therefore the quiet period
uses callback receive time rather than asserting a complete over-the-air packet
history. Callback registration disables HA's cached advertisement replay so
startup does not treat existing cache entries as new button activity. A live
repeat after a restart can still be accepted by the new decoder.

## Remaining research

1. Collect isolated, labeled single, double, long-hold, and release trials with
   generous silent gaps and precise timestamps.
2. Compare multiple units, hardware revisions, and paired/unpaired states.
3. Determine body structure and any keys using legitimately owned hardware.
4. Check address and counter behavior after battery changes and resets.
5. Establish whether advertisements contain explicit gestures or only activity
   notifications for another protocol layer.

Related work, not evidence of support for this exact button:

- [AiDot BLE local control](https://github.com/bermantanner/aidot-ble-local-control)
  researches bulb GATT behavior.
- [BLE ADV](https://github.com/NicoIIT/ha-ble-adv) provides infrastructure for
  supported proprietary advertising remotes.

If enough of the protocol becomes known, the pure parser can become a separate
library or support can be proposed upstream. For now, a small custom integration
keeps the experimental scope explicit.
