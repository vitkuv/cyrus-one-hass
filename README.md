# Cyrus ONE

Home Assistant integration for controlling **Cyrus ONE** and **Cyrus ONE HD** amplifiers over Bluetooth Low Energy (BLE). 

This completely replaces the official **Cyrus ONE Remote** mobile application, which is no longer supported and is no longer available in app stores.

Pair this component with a smart plug to create a truly modern smart device.

## Prerequisites

- A Cyrus ONE or Cyrus ONE HD amplifier
- A Home Assistant instance with Bluetooth capabilities (built-in Bluetooth, USB dongle, or [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/))

## Installation

### Via HACS (recommended)

1. Add this repository as a custom repository in HACS:
   - Go to **HACS → Integrations → Three-dot menu → Custom repositories**
   - Repository: `https://github.com/vitkuv/cyrus-one-hass`
   - Category: **Integration**

2. Click **Install** on the Cyrus ONE integration

3. Restart Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=vitkuv&repository=cyrus-one-hass&category=integration)

### Manual installation

1. Copy the `custom_components/cyrus_one/` directory into your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

No manual configuration is needed. The integration uses **Bluetooth discovery** — your Cyrus ONE/ONE HD amplifier will be detected automatically.

If a device is not found automatically, ensure:
- Bluetooth is enabled on your Home Assistant host
- The amplifier is powered on and within range
- The amplifier's BLE name starts with `ONE-`
## Supported entities

| Platform | Description |
|---|---|
| **Media Player** | Volume, mute, source selection |
| **Switch** | AV Direct mode toggle |
| **Number** | Balance control |
| **Button** | Display brightness up/down |
| **Binary Sensor** | Headphone connection status |

## Support

Report issues at [github.com/vitkuv/cyrus-one-hass/issues](https://github.com/vitkuv/cyrus-one-hass/issues).
