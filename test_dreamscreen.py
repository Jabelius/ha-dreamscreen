"""Self-check for the vendored DreamScreen protocol. Run: python test_dreamscreen.py"""
import crc8

from custom_components.dreamscreen.pydreamscreen import SideKick, get_device
from custom_components.dreamscreen.pydreamscreen.devices import _ReceiveStateMessages


def fake_sidekick_payload():
    """Minimal state payload: SideKick, ambient mode, 55%, teal, scene 3."""
    p = bytearray(80)
    p[0:16] = b"Sidekick Left".ljust(16, b"\x00")
    p[16:32] = b"Living Room".ljust(16, b"\x00")
    p[32] = 0           # group number
    p[33] = 3           # mode: ambient
    p[34] = 55          # brightness
    p[40:43] = bytes((0x40, 0xE0, 0xD0))
    p[62] = 3           # scene: ocean
    p[-2] = 3           # device type: SideKick
    return bytes(p)


def test_parse():
    state = _ReceiveStateMessages.parse_message(fake_sidekick_payload(), "10.0.0.5")
    assert state["device_type"] == "SideKick", state
    assert state["name"] == "Sidekick Left"
    assert state["group_name"] == "Living Room"
    assert state["mode"] == 3 and state["brightness"] == 55
    assert state["ambient_color"] == b"\x40\xe0\xd0"
    assert state["ambient_scene"] == 3
    device = get_device(state)
    assert isinstance(device, SideKick) and device.ip == "10.0.0.5"
    return device


def test_packet(device):
    packet = device._build_packet(namespace=3, command=1, payload=[3])
    assert packet[0] == 0xFC and packet[1] == 6, packet   # magic, len(payload)+5
    assert packet[2] == 0 and packet[3] == 17, packet     # group 0 -> flags 17
    assert list(packet[4:7]) == [3, 1, 3], packet         # namespace, command, mode
    assert packet[7:] == crc8.crc8(packet[:7]).digest(), packet


if __name__ == "__main__":
    test_packet(test_parse())
    print("ok")
