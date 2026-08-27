"""Low-level interface helpers: list Wi-Fi interfaces, read/set MAC addresses."""

import os
import random
import re
import subprocess

MAC_RE = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")

# IEEE-registered OUI prefixes are avoided; we set the locally-administered
# bit (bit 1 of the first octet) and clear the multicast bit (bit 0), the
# same trick iOS/macOS use for "private" addresses, so the result never
# collides with a real vendor-assigned MAC on the network.
_LOCALLY_ADMINISTERED_MASK = 0b00000010
_MULTICAST_MASK = 0b00000001


def random_mac() -> str:
    first = random.randint(0, 255)
    first = (first | _LOCALLY_ADMINISTERED_MASK) & ~_MULTICAST_MASK
    octets = [first] + [random.randint(0, 255) for _ in range(5)]
    return ":".join(f"{o:02x}" for o in octets)


def is_valid_mac(mac: str) -> bool:
    return bool(MAC_RE.match(mac))


def list_wifi_interfaces() -> list[str]:
    """Return interface names that have a wireless/phy directory in sysfs."""
    ifaces = []
    net_dir = "/sys/class/net"
    if not os.path.isdir(net_dir):
        return ifaces
    for name in sorted(os.listdir(net_dir)):
        if os.path.isdir(os.path.join(net_dir, name, "wireless")) or os.path.isdir(
            os.path.join(net_dir, name, "phy80211")
        ):
            ifaces.append(name)
    return ifaces


def get_mac(iface: str) -> str | None:
    path = f"/sys/class/net/{iface}/address"
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def _nmcli_managed(iface: str) -> bool:
    if not _has("nmcli"):
        return False
    r = _run(["nmcli", "-t", "-f", "DEVICE,STATE", "device"])
    return any(line.startswith(f"{iface}:") for line in r.stdout.splitlines())


def _has(binary: str) -> bool:
    return subprocess.run(["which", binary], capture_output=True).returncode == 0


def set_mac(iface: str, mac: str) -> tuple[bool, str]:
    """Set the interface MAC address, bringing it down/up as needed.

    Returns (success, message).
    """
    if not is_valid_mac(mac):
        return False, f"'{mac}' is not a valid MAC address"

    managed_by_nm = _nmcli_managed(iface)

    if managed_by_nm and _has("nmcli"):
        # nmcli can set the device down/up itself and re-associate cleanly.
        r = _run(["nmcli", "device", "disconnect", iface])
        set_r = _run(["ip", "link", "set", "dev", iface, "address", mac])
        if set_r.returncode != 0:
            _run(["nmcli", "device", "connect", iface])
            return False, set_r.stderr.strip() or "failed to set MAC via ip link"
        _run(["nmcli", "device", "connect", iface])
        return True, "ok"

    down = _run(["ip", "link", "set", "dev", iface, "down"])
    if down.returncode != 0:
        return False, down.stderr.strip() or "failed to bring interface down"

    set_r = _run(["ip", "link", "set", "dev", iface, "address", mac])
    up = _run(["ip", "link", "set", "dev", iface, "up"])

    if set_r.returncode != 0:
        return False, set_r.stderr.strip() or "failed to set MAC via ip link"
    if up.returncode != 0:
        return False, up.stderr.strip() or "failed to bring interface back up"
    return True, "ok"


def is_root() -> bool:
    return os.geteuid() == 0
