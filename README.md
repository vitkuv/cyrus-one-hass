# Cyrus ONE / ONE HD Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![HA Version](https://img.shields.io/badge/Home%20Assistant-2026.1%2B-blue.svg)

Home Assistant integration to control **Cyrus ONE** and **Cyrus ONE HD** amplifiers via Bluetooth Low Energy (BLE). 

This integration serves as a complete, modern replacement for the official **Cyrus ONE Remote** mobile app, which is no longer supported and has been removed from official app stores.

> 💡 **Smart Home Tip:** Pair this integration with a smart plug (e.g., Sonoff, Shelly, Tuya) for power management. By combining BLE control with automated power supply, you can transform your classic Cyrus amplifier into a fully automated smart device.

---

## Features

Instead of cluttering your dashboard with separate raw sensors, this integration exposes native Home Assistant platforms:

* **Full Media Control:** Volume adjustment, mute toggle, and input source selection.
* **AV Direct Mode:** Quick switch toggle for integration with Home Theater receivers.
* **Balance Adjustment:** Fine-tune left/right balance directly from the UI.
* **Display Management:** Controls for amplifier LED brightness.
* **Headphone Detection:** Binary sensor indicating whether headphones are connected (muting the main speakers).

---

## Prerequisites

* **Supported Hardware:** Cyrus ONE or Cyrus ONE HD amplifier.
* **Bluetooth Connectivity:** A Home Assistant instance with a working Bluetooth stack (built-in Bluetooth, USB Bluetooth dongle, or an [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy/)).

---

## Installation

### Method 1: Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on **Integrations** -> **Three-dot menu** (top right) -> **Custom repositories**.
3. Paste the repository URL: `https://github.com/vitkuv/cyrus-one-hass`
4. Select **Integration** as the category and click **Add**.
5. Find the **Cyrus ONE** integration and click **Download**.
6. **Restart** Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=vitkuv&repository=cyrus-one-hass&category=integration)

### Method 2: Manual Installation

1. Download the latest release archive.
2. Copy the `custom_components/cyrus_one/` directory into your Home Assistant's `custom_components/` folder.
3. **Restart** Home Assistant.

---

## Configuration

This integration supports **Bluetooth Discovery**. 

1. Ensure your amplifier is turned on and within BLE range.
2. Home Assistant should automatically detect the device and show a notification in the UI.
3. If it doesn't appear automatically, go to **Settings** -> **Devices & Services** -> **Add Integration** and search for **Cyrus ONE**.

### Troubleshooting
If the device is not discovered:
* Verify that the amplifier's BLE broadcast name starts with `ONE-`.
* Ensure your Home Assistant Bluetooth adapter is functional and not blocked by a metal case.