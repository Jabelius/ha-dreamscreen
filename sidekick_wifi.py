"""Join a DreamScreen SideKick (in setup AP mode) to your wifi.

Connect this PC to the SideKick's own wifi network first, then:

    python sidekick_wifi.py --ssid "MyWifi" --password "hunter2"

Protocol reverse-engineered from the DreamScreen Android app (NewDeviceFragment):
unicast to 192.168.4.1:8888, write namespace 1 command 1 = SSID, command 2 =
password; device replies with command 0x010D once it has joined.
Only 2.4 GHz networks work, and the SSID must be <= 31 characters.
"""
import argparse
import socket
import time

import crc8

AP_IP = "192.168.4.1"
PORT = 8888


def packet(cmd1, cmd2, payload):
    """Build a DreamScreen write packet."""
    data = bytearray([0xFC, len(payload) + 5, 0xFF, 0x01, cmd1, cmd2])
    data.extend(payload)
    data.extend(crc8.crc8(bytes(data)).digest())
    return bytes(data)


def join(ssid, password, ip=AP_IP, timeout=45):
    """Send credentials, wait for the device to confirm it joined."""
    ssid = ssid.encode("utf8")
    password = password.encode("utf8")
    if len(ssid) > 31:
        raise ValueError("SSID too long for the device (max 31 bytes)")

    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("", PORT))
    listener.settimeout(timeout)

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Same order and pacing the app uses; the SSID is sent twice on purpose.
    for cmd1, cmd2, payload, delay in (
        (3, 1, b"\x00", 0.03),
        (1, 1, ssid, 0.03),
        (1, 1, ssid, 0.03),
        (1, 2, password, 0),
    ):
        sender.sendto(packet(cmd1, cmd2, payload), (ip, PORT))
        time.sleep(delay)
    sender.close()

    # 0x0114 = credentials received, 0x010D = joined the network. Only the
    # second one means success; the device sends the first either way.
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            message, (addr, _) = listener.recvfrom(1024)
            if len(message) < 6 or message[0] != 0xFC:
                continue
            command = (message[4], message[5])
            print("  device replied {:02X}{:02X}{}".format(
                command[0], command[1],
                " (credentials received)" if command == (0x01, 0x14) else ""))
            if command == (0x01, 0x0D):
                return addr
    except socket.timeout:
        pass
    finally:
        listener.close()
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssid", required=True, help="your 2.4 GHz wifi name")
    parser.add_argument("--password", required=True)
    parser.add_argument("--ip", default=AP_IP, help="SideKick setup IP")
    args = parser.parse_args()

    print("Sending credentials to {}...".format(args.ip))
    result = join(args.ssid, args.password, args.ip)
    if result:
        print("SideKick confirmed, it joined your wifi.")
    else:
        print("Not joined. If you only saw 0114, the device got the credentials "
              "but could not connect - almost always a wrong password. The "
              "network must also be 2.4 GHz and WPA2, not WPA3.")
