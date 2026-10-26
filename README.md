# Linkind BLE Button for Home Assistant

[![Release](https://img.shields.io/github/v/release/RitwikGupta/ha-linkind-ble)](https://github.com/RitwikGupta/ha-linkind-ble/releases)
[![Validate](https://github.com/RitwikGupta/ha-linkind-ble/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/RitwikGupta/ha-linkind-ble/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/RitwikGupta/ha-linkind-ble)](LICENSE)

Use a **Linkind HCRZ12FBM071** Bluetooth button in Home Assistant. Button activity
shows up as an event you can use to toggle lights, run a script, or start another
automation.

It works through Home Assistant's Bluetooth integration, including
[ESPHome Bluetooth proxies](https://esphome.io/components/bluetooth_proxy/).
You don't need an AiDot account or bulb.

## Requirements

- Home Assistant **2026.10.4 or newer**.
- A Bluetooth adapter or ESPHome proxy connected to HA and within range of the
  button. If you use a proxy, your HA host doesn't need its own Bluetooth adapter.

## Installation

### HACS (recommended)

[![Add Linkind BLE Button to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=RitwikGupta&repository=ha-linkind-ble&category=integration)

Click the button above, download **Linkind BLE Button** in HACS, and restart Home
Assistant.

To add the repository yourself:

1. Open **HACS → ⋮ → Custom repositories**.
2. Enter `https://github.com/RitwikGupta/ha-linkind-ble` and choose the
   **Integration** category.
3. Find **Linkind BLE Button** and download the latest release.
4. **Restart Home Assistant.**

This integration isn't in the default HACS catalog yet.

### Manual

1. Download and extract the source ZIP from the
   [latest release](https://github.com/RitwikGupta/ha-linkind-ble/releases/latest).
2. Copy `custom_components/linkind_ble/` from the extracted files into your HA
   configuration directory's `custom_components/` folder. The final path should
   be `<config>/custom_components/linkind_ble/manifest.json`.
3. **Restart Home Assistant.**

## Setup

1. Press the button near your Bluetooth receiver.
2. Go to **Settings → Devices & services** and click **Configure** on the
   discovered Linkind button. You can also use **Add integration → Linkind BLE
   Button** to select it yourself.
3. Confirm the button's address.

The device page will now have a **Button activity** entity.

## Automate

In the automation editor, select **Button activity**, choose the **received**
trigger, and set the event type to **Activity**. Then add whatever action you want
the button to run.

This example toggles a light group. Replace both entity IDs with your own:

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

The entity shows the time of the last activity. Its attributes also include the
frame counter and Bluetooth signal strength (`rssi`).

## Current support

This is still experimental and has been tested with one HCRZ12FBM071. All detected
actions produce the same `activity` event. Separate single-press, double-press,
hold, and on/off events aren't available yet, nor is a battery reading.

The [protocol notes](docs/protocol.md) cover what we've found so far, how repeated
messages are filtered, and what still needs testing.

## Troubleshooting

If no button appears during setup, check that HA can see your Bluetooth adapter
or proxy, move the button closer, and press it again.

If events aren't arriving, watch **Button activity** on the device page while
pressing the button. This helps narrow down whether the problem is reception or
the automation.

For other problems, [open an issue](https://github.com/RitwikGupta/ha-linkind-ble/issues)
with your HA version, button model, receiver type, and what happened. You can
download integration diagnostics from its entry in **Devices & services**.

## Remove

Delete the integration entry in **Settings → Devices & services**, then remove
the download in HACS and restart HA. If you installed it manually, delete the
`custom_components/linkind_ble/` folder instead.

## Development and protocol research

See [CONTRIBUTING.md](CONTRIBUTING.md) to run the tests or help decode more of the
button's messages.

Licensed under [MIT](LICENSE).
