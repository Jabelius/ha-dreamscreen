"""Self-check for the vendored DreamScreen protocol. Run: python test_dreamscreen.py"""
import crc8

from custom_components.dreamscreen.pydreamscreen import SideKick, get_device
from custom_components.dreamscreen.pydreamscreen.devices import _ReceiveStateMessages

# Captured from a real SideKick: name "SideKick Right", group 2, ambient mode,
# brightness 0x50 (80), colour 0a c8 1e, scene 1. Its state payload is 63 bytes
# and carries no zone fields, so colour and scene sit earlier than on an HD/4K.
REAL_SIDEKICK_STATE = bytes.fromhex(
    "536964654b69636b2052696768740000"
    "504300000000000000000000000000000203500ac81effffff"
    "040403020c01000000000000000000000301000103c2"
)


def test_parse_sidekick():
    assert len(REAL_SIDEKICK_STATE) == 63, len(REAL_SIDEKICK_STATE)
    state = _ReceiveStateMessages.parse_message(REAL_SIDEKICK_STATE, "192.168.1.56")
    assert state["device_type"] == "SideKick", state
    assert state["name"] == "SideKick Right", state
    assert state["group_number"] == 2 and state["mode"] == 3, state
    assert state["brightness"] == 80, state
    assert state["ambient_color"] == b"\x0a\xc8\x1e", state   # index 35-37, not 40-42
    assert state["ambient_scene"] == 1, state                 # index 60, not 62
    device = get_device(state)
    assert isinstance(device, SideKick) and device.ip == "192.168.1.56"
    return device


def test_short_message_rejected():
    assert _ReceiveStateMessages.parse_message(b"\x00" * 20, "192.168.1.56") is None


def test_packet(device):
    packet = device._build_packet(namespace=3, command=1, payload=[3])
    assert packet[0] == 0xFC and packet[1] == 6, packet   # magic, len(payload)+5
    assert packet[2] == 2, packet                         # group number
    assert list(packet[4:7]) == [3, 1, 3], packet         # namespace, command, mode
    assert packet[7:] == crc8.crc8(packet[:7]).digest(), packet


if __name__ == "__main__":
    test_short_message_rejected()
    test_packet(test_parse_sidekick())
    print("ok")
