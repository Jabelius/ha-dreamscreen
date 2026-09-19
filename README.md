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
