# Linkind BLE Button for Home Assistant

An experimental, local Home Assistant custom integration for the **Linkind
HCRZ12FBM071** Bluetooth button. It turns observed button radio activity into a
native `event` entity, received by a Home Assistant Bluetooth adapter or an
[ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/).

No AiDot account, compatible bulb, Mac listener, or button firmware changes are
needed. This is an independent community project, unaffiliated with Linkind,
AiDot, or Home Assistant.

## What works

- Discovery of candidate advertisements, followed by confirmation of the model
  and Bluetooth address.
- One device and **Button activity** event entity per configured button.
- One `activity` event per new matching frame, suppressing repeated frames across
  Bluetooth receivers with a ten-second quiet period.
- Local push updates, unloading/reloading, translated UI strings, and diagnostics
  that exclude device addresses and advertisement contents.

**This is an activity detector, not a complete command decoder.** Normal front
button presses have produced distinct frames in live tests on one physical unit.
Single press, double press, hold, on/off intent, and battery level are **not
decoded**. Mixed gesture testing has not established a reliable mapping. Do not
configure separate gesture actions from this integration yet.

The manufacturer field and frame layout may also occur in other products. Only
confirm discovery if you have identified your HCRZ12FBM071. Other Linkind models,
including Zigbee remotes, are outside the current support scope.

## Requirements

- Home Assistant **2026.10.4 or newer**. This is the tested minimum and provides
  the Bluetooth callback replay control used here.
- A working [Home Assistant Bluetooth integration](https://www.home-assistant.io/integrations/bluetooth/),
  using a local receiver or an ESPHome proxy within range of the button.
- A Linkind HCRZ12FBM071 that emits the documented advertisement format.

The integration only listens to advertisements. Active Bluetooth connections are
not required, and the HA host itself does not need a Bluetooth radio when a proxy
is available.

## Install

### HACS custom repository

1. In HACS, open **Custom repositories** and add
   `https://github.com/RitwikGupta/ha-linkind-ble` as type **Integration**.
2. Download **Linkind BLE Button**. If using the first experimental release,
   enable pre-release versions in HACS when choosing a version.
3. Restart Home Assistant.
4. Press the button near a receiver. In **Settings → Devices & services**, open
   the discovered candidate and confirm its address and model.

This repository is intended for HACS custom-repository installation; it is not
listed in the default HACS catalog.

### Manual installation

Copy `custom_components/linkind_ble` from this repository to
`<your HA config directory>/custom_components/linkind_ble`, then restart HA.
Use the discovery flow above, or **Add integration → Linkind BLE Button** after
pressing the button.

Identify the address in HA's Bluetooth advertisement monitor: press the button
and look for changing manufacturer data under `0x1511` / `5393`. The first byte
changes between actions. Never select an unrelated device just because it has
the same manufacturer field.

## Automate

Find the new **Button activity** entity on the integration's device page. In the
automation editor choose an event entity's **received** trigger and event type
**Activity**, then select the action you want.

For example, replace both entity IDs below with your own. This toggles a light
group on any detected activity; it does not infer an on/off command from the
button.

```yaml
alias: Linkind activity toggles lights
triggers:
  - trigger: event.received
    target:
      entity_id: event.linkind_button_ddee01_button_activity
    options:
      event_type:
        - activity
actions:
  - action: light.toggle
    target:
      entity_id: light.example_room
mode: single
```

The entity's state is the last activity timestamp. Attributes include
`event_type: activity`, the observed byte `counter`, and receive `rssi` in dBm.
The counter is diagnostic data, not a gesture, stable press ID, or button number.
Use the event trigger rather than triggering on arbitrary attribute changes.
HA can restore the last timestamp; cached advertisements are not replayed as new
activity when the entity subscribes.

## Limitations and troubleshooting

- **No discovery:** confirm the proxy/adapter is online in HA, move the button
  close to it, press once, and inspect Bluetooth advertisements. Installing this
  integration does not configure the proxy's Wi-Fi or ESPHome API connection.
- **No event yet:** a sleeping button is quiet until it transmits. The integration
  keeps the event entity available while it sleeps; availability does not prove
  that the battery or radio path is healthy.
- **Unexpected or missed actions:** disable your automation and record isolated,
  labeled trials before assuming a gesture mapping. Distinct frames can each
  generate activity; their semantic meaning remains unknown.
- **Repeated frames:** identical complete payloads within ten seconds of their
  last delivered callback are suppressed. The same payload after ten seconds of
  silence is accepted again. This is duplicate filtering, not authentication or
  replay protection. Live retransmissions spanning a restart may still appear
  as fresh activity.
- **Address changes:** address stability after battery replacement or reset has
  not been established. If the address changes, identify and configure the new
  candidate, then remove the old entry.
- **Other hardware/firmware:** only one physical button has been tested. Please
  report additional hardware revisions and labeled results rather than assuming
  compatibility.

For an issue, include the HA version, button model, receiver type, reproduction
steps, and integration diagnostics. Review attachments before sharing them.
Do not upload a full Bluetooth environment capture, home configuration, or keys.

## Remove

Delete the integration entry in **Settings → Devices & services** to stop
listening and remove its entities. Remove the download in HACS, or delete the
`custom_components/linkind_ble` directory, then restart HA to uninstall the code.

## Development and protocol research

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and testing, and
[docs/protocol.md](docs/protocol.md) for observed bytes, evidence limits, and the
remaining research questions. The runtime uses only HA's Bluetooth API; the
parser has no third-party dependencies. All committed packet fixtures are
synthetic.

Licensed under [MIT](LICENSE).
