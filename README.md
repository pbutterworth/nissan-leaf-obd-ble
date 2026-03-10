# Nissan Leaf OBD BLE — Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/pbutterworth/nissan-leaf-obd-ble.svg)](https://github.com/pbutterworth/nissan-leaf-obd-ble/releases)
[![License](https://img.shields.io/github/license/pbutterworth/nissan-leaf-obd-ble.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/pbutterworth/nissan-leaf-obd-ble.svg)](https://github.com/pbutterworth/nissan-leaf-obd-ble/issues)

A [Home Assistant](https://www.home-assistant.io/) custom integration for monitoring **Nissan Leaf** battery data via a Bluetooth Low Energy (BLE) ELM327 OBD-II adapter (such as the [LeLink2](https://www.lelink.net/)).

When your Leaf pulls into the garage, this integration automatically connects over BLE and reads live battery diagnostics — state of charge, state of health, and more — making them available as native Home Assistant sensors for dashboards, automations, and history tracking.

> **Note:** This integration is in active development. See [Known Issues](#known-issues) for current limitations.

---

## Features

- **State of Charge (SoC)** — real-time battery percentage
- **State of Health (SoH)** — long-term battery degradation tracking
- **Battery capacity** — available and total capacity in kWh
- Communicates over **Bluetooth Low Energy** — no Wi-Fi or cloud dependency
- Works with an **ESPHome Bluetooth proxy** (e.g. GL-iNet GL-S10), so your HA host doesn't need to be near the car
- Uses a pure-Python BLE stack built on [`bleak`](https://github.com/hbldh/bleak) — the same library bundled with Home Assistant

---

## Requirements

### Hardware

| Item | Details |
|---|---|
| **LeLink2 ELM327 BLE OBD-II adapter** | Plugs into the Nissan Leaf's OBD-II port. Other ELM327 BLE dongles may also work. |
| **Bluetooth radio** | Either the HA host's built-in Bluetooth, or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) (recommended for garage setups). |

> **Recommended setup:** A GL-iNet **GL-S10** flashed with ESPHome as a Bluetooth proxy placed in/near the garage. This lets your HA host (wherever it lives) receive BLE advertisements from the LeLink2 dongle without needing to be physically close.

### Software

- Home Assistant **2023.6** or later
- [HACS](https://hacs.xyz/) (for HACS installation)

---

## Installation

### Option 1 — HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** and click the three-dot menu (⋮) in the top right.
3. Select **Custom repositories**.
4. Paste the repository URL:
   ```
   https://github.com/pbutterworth/nissan-leaf-obd-ble
   ```
   and set the category to **Integration**. Click **Add**.
5. Find **Nissan Leaf OBD BLE** in the HACS integration list and click **Download**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & Services → Add Integration**, search for **Nissan Leaf OBD BLE**, and follow the setup wizard.

### Option 2 — Manual

1. Download the [latest release](https://github.com/pbutterworth/nissan-leaf-obd-ble/releases/latest) or clone this repository.
2. Copy the `custom_components/nissan_leaf_obd_ble` folder into your Home Assistant `config/custom_components/` directory:
   ```
   config/
   └── custom_components/
       └── nissan_leaf_obd_ble/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── sensor.py
           └── ...
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration**, search for **Nissan Leaf OBD BLE**, and follow the setup wizard.

---

## Configuration

The integration is configured via the UI (Config Flow). You will be prompted for:

- **BLE device address** — the MAC address of your LeLink2 / ELM327 adapter (e.g. `AA:BB:CC:DD:EE:FF`). You can find this in **Settings → Devices & Services → Bluetooth** after bringing the LeLink2 dongle within range.
- **Scan interval** — how often (in seconds) to attempt a BLE connection and poll data when the device is detected.

After setup, open the device and click **Configure** to adjust **polling intervals** (fast / slow / extra-slow), **cache behaviour** (keep sensor values when out of range), and **BLE UUIDs** (service, read characteristic, write characteristic). Use the UUID options if your dongle uses different GATT UUIDs than the default LeLink ones; see [Other dongles and automatic discovery](#other-dongles-and-automatic-discovery) below.

---

## Other dongles and automatic discovery

**Automatic Bluetooth discovery** (when a device appears in HA’s “Discovered” list and this integration is suggested) is driven by the integration’s **manifest**. Home Assistant only offers this integration for BLE devices that **advertise** a service UUID listed in `manifest.json` under the `bluetooth` array. By default, only the LeLink service UUID (`0000ffe0-0000-1000-8000-00805f9b34fb`) is listed.

**Using a dongle with different GATT UUIDs**

- You can still add the integration manually: **Settings → Devices & Services → Add Integration** → **Nissan Leaf OBD BLE**, then pick your device from the list (devices are filtered by local name “OBDBLE”). After adding, open the device, click **Configure**, and set the three BLE UUIDs (service, read characteristic, write characteristic) to match your dongle so the connection works.

**Making automatic discovery work for another dongle**

- If your dongle advertises a **different** service UUID and you want it to show up in “Discovered” for this integration, you can **manually edit** the integration’s `manifest.json` after installation:
  1. Open `config/custom_components/nissan_leaf_obd_ble/manifest.json` on your Home Assistant host.
  2. Add another object to the `bluetooth` array with your dongle’s advertised `service_uuid`. Example:

     ```json
     "bluetooth": [
       { "service_uuid": "0000ffe0-0000-1000-8000-00805f9b34fb" },
       { "service_uuid": "YOUR_OTHER_DONGLE_SERVICE_UUID" }
     ]
     ```

  3. Restart Home Assistant so discovery picks up the change.
- **Note:** HACS or a manual update of the integration may overwrite `manifest.json`; you may need to re-apply this edit after updating unless multiple UUIDs are added to the integration in a future release.

---

## Entities

Once set up, the integration creates a **device** for your Nissan Leaf and exposes the following **sensor entities**:

| Entity | Unit | Description |
|---|---|---|
| `sensor.nissan_leaf_state_of_charge` | `%` | Current traction battery charge level |
| `sensor.nissan_leaf_state_of_health` | `%` | Battery health / degradation indicator |
| `sensor.nissan_leaf_battery_capacity` | `kWh` | Available (usable) battery capacity |

> More entities may be added as the integration matures. See open issues and the [HA Community thread](https://community.home-assistant.io/t/custom-component-nissan-leaf-via-lelink-2-elm327-ble/561961) for the latest status.

---

## How It Works

The LeLink2 dongle tunnels the ELM327 serial protocol over BLE GATT. This integration includes a custom `bleserial` module that wraps Home Assistant's bundled [`bleak`](https://github.com/hbldh/bleak) client to expose a `pySerial`-like interface. On top of that, a modified [`python-OBD`](https://github.com/brendan-w/python-OBD) layer handles ELM327 command formatting, ISO 15765-4 CAN framing, and flow control — producing decoded Leaf-specific PID responses that are then published as HA sensor states.

```
Nissan Leaf CAN bus
        │
  OBD-II port
        │
  LeLink2 dongle  ◄──── BLE ────►  ESPHome Bluetooth Proxy  ◄──── Wi-Fi ────►  Home Assistant
                                          (GL-S10)                               nissan_leaf_obd_ble
```

---

## Troubleshooting

**The integration can't find my LeLink2 adapter**
- Confirm the dongle is plugged in and powered (ignition on or accessory mode).
- Check **Settings → Devices & Services → Bluetooth** in HA to verify the adapter is advertising.
- If using an ESPHome Bluetooth proxy, ensure it's online and the proxy component is enabled.

**Sensors show `unavailable` after the car leaves**
- This is expected behaviour. The integration only polls when the BLE device is in range.

**No data / sensors stuck**
- Enable debug logging and check the HA logs for `custom_components.nissan_leaf_obd_ble`:
  ```yaml
  # configuration.yaml
  logger:
    default: warning
    logs:
      custom_components.nissan_leaf_obd_ble: debug
  ```
- Share logs in the [HA Community thread](https://community.home-assistant.io/t/custom-component-nissan-leaf-via-lelink-2-elm327-ble/561961) or [open an issue](https://github.com/pbutterworth/nissan-leaf-obd-ble/issues).

---

## Known Issues

- The integration is under active development and may have rough edges.
- Newer Nissan Leaf models (ZE1 / Gen 2 onwards) do not have background CAN traffic at the OBD port — the car must be on for data to be polled.
- Only the LeLink2 BLE adapter has been tested; other ELM327 BLE adapters may work but are untested.

---

## Contributing

Contributions are very welcome! Please:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-new-sensor`).
3. Commit your changes and open a Pull Request.

Bug reports and feature requests can be filed as [GitHub Issues](https://github.com/pbutterworth/nissan-leaf-obd-ble/issues).

---

## Related Resources

- [HA Community discussion thread](https://community.home-assistant.io/t/custom-component-nissan-leaf-via-lelink-2-elm327-ble/561961)
- [My Nissan Leaf Forum — BLE / LeLink2 libraries](https://mynissanleaf.com/threads/ble-lelink2-leaf-open-source-libraries.34904/)
- [Official Home Assistant Nissan Leaf integration](https://www.home-assistant.io/integrations/nissan_leaf/) (cloud-based, older models only)
- [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy.html)

---

## License

This project is licensed under the [MIT License](LICENSE).
