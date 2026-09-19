# DreamScreen for Home Assistant (SideKick / HD / 4K)

Fork of the archived [J3n50m4t/Home-Assistant-DreamScreen-Service](https://github.com/J3n50m4t/Home-Assistant-DreamScreen-Service),
with `pydreamscreen` vendored and `netifaces` removed (it has no Python 3.13 wheels,
so the original can no longer install on current Home Assistant).

Exposes each device as a **light** entity: on/off, brightness, RGB colour, and
effects (Video / Music / the 9 ambient scenes).

## Install

1. Copy `custom_components/dreamscreen/` into your HA `/config/custom_components/`.
2. Add to `configuration.yaml`, one block per SideKick:

```yaml
light:
  - platform: dreamscreen
    host: 192.168.1.50
    name: Sidekick Left
  - platform: dreamscreen
    host: 192.168.1.51
    name: Sidekick Right
    timeout: 4        # optional, raise on a busy wifi
```

3. Restart Home Assistant.

Devices need static IPs (DHCP reservation) — there is no discovery.

## Check

`python test_dreamscreen.py` (needs `pip install crc8`) — verifies state parsing
and command packet/CRC building without Home Assistant.

## Device notes (measured on a SideKick, firmware Side2Side revE)

* The SideKick is an ESP8266. In setup mode it is an access point, `192.168.4.1`.
* It serves the stock Arduino OTA form at `http://192.168.4.1/firmware`, HTTP basic
  auth `admin` / `DSadmin714` (credentials are hardcoded in the DreamScreen app).
* **OTA is capped at ~128 KB.** Free sketch space is the total sketch area minus the
  293 KB running sketch, so uploads abort at exactly 130825 bytes — the stock image
  itself is too big to re-flash, and DreamScreen's own `Sidekick_WLED_0.11.1.bin`
  (649 KB) cannot be installed this way. Converting one to WLED needs serial access.
  A failed OTA is harmless: the ESP8266 stages the new image in free flash and only
  swaps it in on success.
* `0x01 0x11` ("Stop ESP Drivers") does not lift the cap.
* Firmware images and protocol docs: https://github.com/d8ahazard/DreamscreenDocs

## SideKick state layout

The upstream library never actually worked with a SideKick. Two fixes here, both
verified against real hardware:

* Its state message is 63 bytes, but upstream only accepted replies whose length
  byte was `0x90-0xFF`, so every SideKick reply was discarded and the device
  looked absent.
* A SideKick carries no zone fields, so ambient colour is at payload index 35-37
  (not 40-42) and ambient scene at index 60 (not 62).

## Multiple devices

Devices always reply to UDP port 8888 regardless of the source port, so every
listener must bind that one port. Two devices polling at once meant one socket
swallowed the other's reply and that light went missing, so state reads are
serialised behind a lock. A device that does not answer during startup now
raises `PlatformNotReady`, so Home Assistant retries instead of dropping the
light until the next restart.
